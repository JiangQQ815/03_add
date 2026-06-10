# Batch Installer

## 功能说明

一键批量安装多个软件包，支持：
- EXE 安装程序
- MSI 安装包
- Python 脚本
- 按顺序自动安装
- 安装完成后自动配置系统环境变量

## 目录结构

```
batch_installer/
├── config.txt        # 配置文件（定义安装顺序和环境变量）
├── main.py           # 主程序
├── run.bat           # 运行脚本（需管理员权限）
├── README.txt        # 说明文档
├── packages/         # 安装包文件夹（放入你的安装包）
│   ├── Python37/
│   │   └── python-3.7.x.exe
│   ├── Python27/
│   │   └── python-2.7.x.msi
│   ├── SoftwareA/
│   │   └── setup.exe
│   └── SoftwareB/
│       └── installer.msi
└── logs/             # 安装日志（自动生成）
```

## 配置说明

### 安装包配置

```ini
[PackageName]
InstallPath=packages\PackageName
InstallArgs=/silent /norestart
EnvVars=VAR_NAME
```

- `InstallPath`: 安装包所在文件夹（相对于项目根目录）
- `InstallArgs`: 安装参数（/silent, /S, /quiet 等）
- `EnvVars`: 安装后需要设置的环境变量名

### 环境变量配置

```ini
[EnvironmentVariables]
VAR_NAME=value
PathEntries=path1,path2,path3
```

- `VAR_NAME=value`: 设置环境变量
- `PathEntries`: 添加到系统 PATH

## 使用方法

1. 将安装包放入 `packages` 文件夹下的对应子文件夹
2. 修改 `config.txt` 配置安装顺序和参数
3. **右键 run.bat → 以管理员身份运行**
4. 等待安装完成，查看 `logs` 文件夹中的日志

## 注意事项

- 需要管理员权限运行
- 安装前请先测试安装包的静默安装参数
- 建议先在虚拟机中测试