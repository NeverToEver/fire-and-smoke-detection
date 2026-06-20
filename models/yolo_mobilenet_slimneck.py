"""Slim-Neck 变体 — GSConv + VoVGSCSP 轻量化特征融合颈。作为可选架构保留。"""

import torch
import torch.nn as nn
from ultralytics.nn.modules.conv import Conv
import ultralytics.nn.tasks as tasks
from ultralytics.nn.modules.head import Detect as UltralyticsDetect

from .backbone import MobileNetV3_Backbone  # noqa: F401 — 重导出供 YAML 引用


# ----------------- Slim-Neck 核心组件 -----------------

class GSConv(nn.Module):
    """Ghost Shuffle Convolution — 轻量化卷积模块。

    通过分组卷积 + 通道重排实现特征图生成，减少计算量。
    参考: https://arxiv.org/abs/2211.05322
    """

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        super().__init__()
        c_ = c2 // 2
        self.cv1 = Conv(c1, c_, k, s, p, g, d, act)  # 主卷积
        self.cv2 = Conv(c_, c_, 5, 1, None, c_, d, act)  # 深度可分离卷积

    def forward(self, x):
        x1 = self.cv1(x)
        x2 = torch.cat((x1, self.cv2(x1)), 1)
        # 通道重排：将 2 组特征交错排列
        b, n, h, w = x2.size()
        y = x2.reshape(b, 2, n // 2, h, w)
        y = y.permute(0, 2, 1, 3, 4)
        return y.reshape(b, n, h, w)


class GSBottleneck(nn.Module):
    """GSConv Bottleneck — 轻量化残差瓶颈模块。"""

    def __init__(self, c1, c2, k=3, s=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.conv_lighting = nn.Sequential(
            GSConv(c1, c_, 1, 1),  # 1x1 降维
            GSConv(c_, c2, 3, s, act=False),  # 3x3 卷积
        )
        self.shortcut = Conv(c1, c2, 1, 1, act=False)  # 残差连接

    def forward(self, x):
        return self.conv_lighting(x) + self.shortcut(x)


class VoVGSCSP(nn.Module):
    """VoV-GSCSP 模块 — 基于 GSConv 的跨阶段部分连接。

    用于 Slim-Neck 的特征融合，比标准 C3k2 更轻量。
    """

    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, 1, 1)  # 分支 1
        self.cv2 = Conv(c1, c_, 1, 1)  # 分支 2
        self.gsb = nn.Sequential(*(GSBottleneck(c_, c_, e=1.0) for _ in range(n)))
        self.cv3 = Conv(2 * c_, c2, 1)  # 合并

    def forward(self, x):
        x1 = self.gsb(self.cv1(x))
        y = self.cv2(x)
        return self.cv3(torch.cat((x1, y), 1))


# ----------------- Slim-Neck Head -----------------

class YOLOv11_MobileNetV3_SlimNeck_Head(nn.Module):
    """Slim-Neck 颈部网络 — 使用 GSConv + VoVGSCSP 替代标准 Conv + C3k2。

    结构与标准 Head 相同（FPN + PAN），但使用更轻量的模块，
    适合边缘设备部署。
    """

    def __init__(self, ch=None):
        super().__init__()
        if ch is None:
            ch = [24, 40, 80, 160]
        p2, p3, p4, p5 = ch

        # Top-down FPN: 自顶向下融合高层语义信息
        self.up_p5 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p4 = VoVGSCSP(p5 + p4, 256, 1)

        self.up_p4 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p3 = VoVGSCSP(256 + p3, 128, 1)

        self.up_p3 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p2 = VoVGSCSP(128 + p2, 64, 1)

        # Bottom-up PAN: 自底向上融合底层位置信息
        self.down_p2 = GSConv(64, 64, 3, 2)
        self.c3_p3_out = VoVGSCSP(64 + 128, 128, 1)

        self.down_p3 = GSConv(128, 128, 3, 2)
        self.c3_p4_out = VoVGSCSP(128 + 256, 256, 1)

        self.down_p4 = GSConv(256, 256, 3, 2)
        self.c3_p5_out = VoVGSCSP(256 + p5, 256, 1)

        self.channels = [64, 128, 256, 256]

    def forward(self, x):
        """前向传播：FPN 自顶向下 → PAN 自底向上。"""
        p2, p3, p4, p5 = x

        # FPN: 自顶向下
        p5_up = self.up_p5(p5)
        p4_f = self.c3_p4(torch.cat([p5_up, p4], dim=1))

        p4_up = self.up_p4(p4_f)
        p3_f = self.c3_p3(torch.cat([p4_up, p3], dim=1))

        p3_up = self.up_p3(p3_f)
        p2_f = self.c3_p2(torch.cat([p3_up, p2], dim=1))

        # PAN: 自底向上
        p2_d = self.down_p2(p2_f)
        p3_out = self.c3_p3_out(torch.cat([p2_d, p3_f], dim=1))

        p3_d = self.down_p3(p3_out)
        p4_out = self.c3_p4_out(torch.cat([p3_d, p4_f], dim=1))

        p4_d = self.down_p4(p4_out)
        p5_out = self.c3_p5_out(torch.cat([p4_d, p5], dim=1))

        return [p2_f, p3_out, p4_out, p5_out]


# ----------------- 注册到 ultralytics 任务字典 -----------------

_register = {
    "MobileNetV3_Backbone": MobileNetV3_Backbone,
    "YOLOv11_MobileNetV3_SlimNeck_Head": YOLOv11_MobileNetV3_SlimNeck_Head,
    "GSConv": GSConv,
    "VoVGSCSP": VoVGSCSP,
}
for _name, _cls in _register.items():
    tasks.__dict__[_name] = _cls
