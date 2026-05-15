import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
from ultralytics.nn.modules.conv import Conv
from ultralytics.nn.modules.block import C3k2
import ultralytics.nn.tasks as tasks
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules.head import Detect as UltralyticsDetect


# ----------------- MobileNetV3 Backbone -----------------

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


# ----------------- YOLOv11 Head (标准 Conv + C3k2) -----------------

class YOLOv11_MobileNetV3_Head(nn.Module):
    def __init__(self, ch=None):
        super().__init__()
        if ch is None:
            ch = [24, 40, 80, 160]
        p2, p3, p4, p5 = ch

        # Top-down FPN
        self.up_p5 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p4 = C3k2(p5 + p4, 256, n=1)

        self.up_p4 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p3 = C3k2(256 + p3, 128, n=1)

        self.up_p3 = nn.Upsample(scale_factor=2, mode='nearest')
        self.c3_p2 = C3k2(128 + p2, 64, n=1)

        # Bottom-up PAN
        self.down_p2 = Conv(64, 64, k=3, s=2)
        self.c3_p3_out = C3k2(64 + 128, 128, n=1)

        self.down_p3 = Conv(128, 128, k=3, s=2)
        self.c3_p4_out = C3k2(128 + 256, 256, n=1)

        self.down_p4 = Conv(256, 256, k=3, s=2)
        self.c3_p5_out = C3k2(256 + p5, 256, n=1)

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


# ----------------- Detect Wrapper -----------------

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


# ----------------- 注册到 ultralytics 任务字典 -----------------

_register = {
    "MobileNetV3_Backbone": MobileNetV3_Backbone,
    "YOLOv11_MobileNetV3_Head": YOLOv11_MobileNetV3_Head,
    "Select": Select,
    "DetectWrapper": DetectWrapper,
}
for _name, _cls in _register.items():
    tasks.__dict__[_name] = _cls
    if tasks.__dict__.get(_name) is not _cls:
        raise RuntimeError(f"模块注册失败: {_name} 被覆盖，可能是 ultralytics 版本不兼容")

# 后向兼容：旧 Slim-Neck 训练的 .pt 权重 pickle 引用本模块下的 VoVGSCSP/GSConv
try:
    from .yolo_mobilenet_slimneck import GSConv, GSBottleneck, VoVGSCSP  # noqa: F401
except ImportError:
    pass
