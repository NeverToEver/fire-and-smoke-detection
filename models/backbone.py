"""MobileNetV3 Backbone — 共享实现，供 yolo_mobilenet 和 yolo_mobilenet_slimneck 使用。"""

import torch.nn as nn
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights


class MobileNetV3_Backbone(nn.Module):
    """基于 torchvision MobileNetV3-Large 的特征提取骨干网络。

    输出 4 层多尺度特征，通道数为 [24, 40, 80, 160]，
    分别对应 P2/P3/P4/P5 用于目标检测。
    """

    # 特征提取的层索引，对应 MobileNetV3-Large 的不同阶段
    STAGE_INDICES = [2, 4, 7, 13]
    # 各阶段输出通道数
    STAGE_CHANNELS = [24, 40, 80, 160]

    def __init__(self, pretrained=True):
        super().__init__()
        weights = MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        base = mobilenet_v3_large(weights=weights)
        features = base.features
        self.stage_idxs = self.STAGE_INDICES
        self.stages = nn.ModuleList([features[i] for i in range(max(self.stage_idxs) + 1)])
        self.channels = self.STAGE_CHANNELS

    def forward(self, x):
        """前向传播，返回 4 层特征图列表。"""
        outs = []
        for i, layer in enumerate(self.stages):
            x = layer(x)
            if i in self.stage_idxs:
                outs.append(x)
        return outs
