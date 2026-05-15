import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
from ultralytics.nn.modules.conv import Conv
import ultralytics.nn.tasks as tasks
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules.head import Detect as UltralyticsDetect


# ----------------- Slim-Neck 核心组件 -----------------

class GSConv(nn.Module):
    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        super().__init__()
        c_ = c2 // 2
        self.cv1 = Conv(c1, c_, k, s, p, g, d, act)
        self.cv2 = Conv(c_, c_, 5, 1, None, c_, d, act)

    def forward(self, x):
        x1 = self.cv1(x)
        x2 = torch.cat((x1, self.cv2(x1)), 1)
        b, n, h, w = x2.size()
        y = x2.reshape(b, 2, n // 2, h, w)
        y = y.permute(0, 2, 1, 3, 4)
        return y.reshape(b, n, h, w)


class GSBottleneck(nn.Module):
    def __init__(self, c1, c2, k=3, s=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.conv_lighting = nn.Sequential(
            GSConv(c1, c_, 1, 1),
            GSConv(c_, c2, 3, s, act=False)
        )
        self.shortcut = Conv(c1, c2, 1, 1, act=False)

    def forward(self, x):
        return self.conv_lighting(x) + self.shortcut(x)


class VoVGSCSP(nn.Module):
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__()
        c_ = int(c2 * e)
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c1, c_, 1, 1)
        self.gsb = nn.Sequential(*(GSBottleneck(c_, c_, e=1.0) for _ in range(n)))
        self.cv3 = Conv(2 * c_, c2, 1)

    def forward(self, x):
        x1 = self.gsb(self.cv1(x))
        y = self.cv2(x)
        return self.cv3(torch.cat((x1, y), 1))


# ----------------- 你的原有架构 (注入 Slim-Neck) -----------------

class MobileNetV3_Backbone(nn.Module):
    def __init__(self, pretrained=True):
        super().__init__()
        weights = MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        base = mobilenet_v3_large(weights=weights)
        features = base.features
        self.stage_idxs = [2, 4, 7, 13]
        self.stages = nn.ModuleList([features[i] for i in range(max(self.stage_idxs) + 1)])
        self.channels = [24, 40, 80, 160]

    def forward(self, x):
        outs = []
        for i, layer in enumerate(self.stages):
            x = layer(x)
            if i in self.stage_idxs:
                outs.append(x)
        return outs


class YOLOv11_MobileNetV3_Head(nn.Module):
    def __init__(self, ch=None):
        super().__init__()
        if ch is None:
            ch = [24, 40, 80, 160]
        p2, p3, p4, p5 = ch

        # --- Top-down 路径 ---
        self.up_p5 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p4 = VoVGSCSP(p5 + p4, 256, 1)  # 替换 C3k2

        self.up_p4 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p3 = VoVGSCSP(256 + p3, 128, 1)  # 替换 C3k2

        self.up_p3 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p2 = VoVGSCSP(128 + p2, 64, 1)  # 替换 C3k2 (P2极小目标层)

        # --- Bottom-up 路径 ---
        self.down_p2 = GSConv(64, 64, 3, 2)  # 替换普通 Conv
        self.c3_p3_out = VoVGSCSP(64 + 128, 128, 1)

        self.down_p3 = GSConv(128, 128, 3, 2)  # 替换普通 Conv
        self.c3_p4_out = VoVGSCSP(128 + 256, 256, 1)

        self.down_p4 = GSConv(256, 256, 3, 2)  # 替换普通 Conv
        self.c3_p5_out = VoVGSCSP(256 + p5, 256, 1)

        self.channels = [64, 128, 256, 256]

    def forward(self, x):
        p2, p3, p4, p5 = x
        p5_up = self.up_p5(p5)
        p4_f = self.c3_p4(torch.cat([p5_up, p4], dim=1))
        p4_up = self.up_p4(p4_f)
        p3_f = self.c3_p3(torch.cat([p4_up, p3], dim=1))
        p3_up = self.up_p3(p3_f)
        p2_f = self.c3_p2(torch.cat([p3_up, p2], dim=1))

        p2_d = self.down_p2(p2_f)
        p3_out = self.c3_p3_out(torch.cat([p2_d, p3_f], dim=1))
        p3_d = self.down_p3(p3_out)
        p4_out = self.c3_p4_out(torch.cat([p3_d, p4_f], dim=1))
        p4_d = self.down_p4(p4_out)
        p5_out = self.c3_p5_out(torch.cat([p4_d, p5], dim=1))
        return [p2_f, p3_out, p4_out, p5_out]


class Select(nn.Module):
    def __init__(self, idx=0, ch=None):
        super().__init__()
        self.idx = int(idx)
        self.c2 = int(ch) if ch is not None else None

    def forward(self, x):
        return x[self.idx]


class DetectWrapper(UltralyticsDetect):
    def __init__(self, nc=80, *ch):
        ch_list = list(map(int, ch))
        super().__init__(nc=int(nc), ch=ch_list)

    def forward(self, x):
        return super().forward(x)


# 注册到任务字典
_register = {
    "MobileNetV3_Backbone": MobileNetV3_Backbone,
    "YOLOv11_MobileNetV3_Head": YOLOv11_MobileNetV3_Head,
    "Select": Select,
    "DetectWrapper": DetectWrapper,
    "GSConv": GSConv,
    "VoVGSCSP": VoVGSCSP,
}
for _name, _cls in _register.items():
    tasks.__dict__[_name] = _cls
    if tasks.__dict__.get(_name) is not _cls:
        raise RuntimeError(f"模块注册失败: {_name} 被覆盖，可能是 ultralytics 版本不兼容")