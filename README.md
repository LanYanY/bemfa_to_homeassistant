# Home Assistant 巴法云集成

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub release](https://img.shields.io/github/release/yourusername/ha-bemfa.svg)](https://github.com/yourusername/ha-bemfa/releases)
[![License](https://img.shields.io/github/license/yourusername/ha-bemfa.svg)](LICENSE)

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

| 设备类型 | 功能 |
|---------|------|
| 开关 | 开关控制 |
| 灯光 | 开关、亮度调节、色温调节 |
| 风扇 | 开关、速度调节(4档)、摇头控制 |
| 空调 | 开关、温度调节、模式切换、风速调节、扫风控制 |
| 窗帘 | 开关、暂停、位置控制 |
| 传感器 | 温度、湿度、光照、PM2.5、心率等数据监测 |

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
