# Home Assistant 巴法云集成

这是一个用于 Home Assistant 的巴法云集成组件。通过这个组件，你可以在 Home Assistant 中控制和监控你的巴法云设备。

## 功能特点

- 支持多种设备类型:
  - 开关
  - 灯光(支持亮度和色温调节)
  - 风扇(支持速度和摇头控制)
  - 空调(支持温度、模式、风速和扫风控制)
  - 窗帘(支持开关和位置控制)
  - 传感器(温度、湿度、光照等)
- 实时状态更新
- 稳定的 MQTT 连接
- 简单的配置流程

## 安装

### HACS 安装 (推荐)

1. 打开 HACS
2. 点击集成
3. 点击右上角的三个点
4. 选择"添加自定义仓库"
5. 输入仓库地址: `https://github.com/yourusername/ha-bemfa`
6. 选择类别为"集成"
7. 点击"添加"
8. 在 HACS 中搜索"巴法云"并安装

### 手动安装

1. 下载此仓库的最新版本
2. 将 `custom_components/bemfa` 文件夹复制到你的 Home Assistant 配置目录下的 `custom_components` 文件夹中
3. 重启 Home Assistant

## 配置

1. 在 Home Assistant 的配置 -> 集成中点击添加集成
2. 搜索"巴法云"
3. 输入你的巴法云 API 密钥
4. 点击提交

## 支持的设备类型

| 设备类型 | 主题后缀 | 功能和消息格式 |
|---------|---------|----------------|
| 开关/插座 | 006/001 | - 开：`on`<br>- 关：`off` |
| 灯光 | 002 | - 开/关：`on`/`off`<br>- 亮度：`on#亮度值`（范围：1-100）<br>- 颜色：`on#亮度值#rgb值`<br>- 色温：`on#亮度值#色温值`（范围：2700-6500） |
| 风扇 | 003 | - 开/关：`on`/`off`<br>- 档位：`on#档位`（1-4档）<br>- 摇头：`on#档位#1`（开启）<br>  `on#档位#0`（关闭） |
| 空调 | 005 | - 开/关：`on`/`off`<br>- 模式：`on#模式#温度`<br>  模式值：2=制冷，3=制热，4=送风，<br>  5=除湿，6=睡眠，7=节能<br>- 温度范围：16-32°C |
| 窗帘 | 009 | - 开/关：`on`/`off`<br>- 暂停：`pause`<br>- 位置：`on#位置值`（0-100） |
| 传感器 | 004 | 数据格式：`#温度#湿度#开关#光照#pm2.5#心率`<br>（可选参数，但#号必须保留） |

可参考此文档：
- [巴法文档中心-天猫精灵接入](https://cloud.bemfa.com/docs/src/speaker_mall.html)
![image](https://github.com/user-attachments/assets/f2f76bf2-79b0-4481-8bc2-daa436c991d5)


## 主题命名规则

设备类型由主题名称的最后三位数字决定，例如：
- `light002` - 灯光设备
- `fan003` - 风扇设备
- `sensor004` - 传感器
- `ac005` - 空调
- `switch006` - 开关
- `curtain009` - 窗帘

## 常见问题

**Q: 设备无法连接怎么办？**
A: 请检查:
1. API 密钥是否正确
2. 设备是否在线
3. 网络连接是否正常

**Q: 状态更新不及时怎么办？**
A: 可以尝试:
1. 检查网络连接
2. 重启 Home Assistant
3. 重新添加集成

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢
- [larry-wong/bemfa](https://github.com/larry-wong/bemfa) - 感谢这个优秀的开源项目提供的参考和灵感
- [Home Assistant](https://www.home-assistant.io/)
- [巴法云](https://www.bemfa.com/)

## 免责声明

本项目不隶属于巴法云官方。使用本集成时请遵守巴法云的服务条款。 
