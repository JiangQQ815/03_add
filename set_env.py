"""
Environment Variables Setup
从 config.txt 读取配置，设置系统环境变量
支持直接写关键字：
- PATH_Entries: 添加到系统 PATH
- PythonPath: 新建系统变量 PythonPath
- 其他 xxx=yyy格式: 新建用户变量 xxx
"""

import os
import winreg
from datetime import datetime
from typing import Dict, List


class EnvSetup:
    """环境变量设置器"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.path_entries = []
        self.pythonpath_value = None
        self.user_vars = {}
        self.log_lines = []

    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{timestamp}] {message}'
        print(line)
        self.log_lines.append(line)

    def parse_config(self) -> bool:
        """解析配置文件"""
        if not os.path.exists(self.config_path):
            self.log(f'[ERROR] Config file not found: {self.config_path}')
            return False

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            self.log(f'[ERROR] Failed to read config: {str(e)}')
            return False

        for line in lines:
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue

            if '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # PATH_Entries
            if key == 'PATH_Entries':
                paths = [p.strip() for p in value.split(';') if p.strip()]
                for p in paths:
                    if p not in self.path_entries:
                        self.path_entries.append(p)

            # PythonPath 系统变量
            elif key == 'PythonPath':
                self.pythonpath_value = value

            # 用户变量（其他 xxx=yyy 格式）
            else:
                self.user_vars[key] = value

        return True

    def add_to_system_path(self, paths: List[str]) -> tuple:
        """添加路径到系统 PATH"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )

            current_path, _ = winreg.QueryValueEx(key, 'Path')
            winreg.CloseKey(key)

            existing_paths = [p.strip().lower() for p in current_path.split(';') if p.strip()]
            added = []
            skipped = []

            for path in paths:
                path_stripped = path.strip()
                if not path_stripped:
                    continue

                path_normalized = path_stripped.rstrip('\\').lower()

                if path_normalized in existing_paths:
                    skipped.append(path_stripped)
                else:
                    new_path = current_path + ';' + path_stripped
                    key = winreg.OpenKey(
                        winreg.HKEY_LOCAL_MACHINE,
                        r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                        0,
                        winreg.KEY_READ | winreg.KEY_WRITE
                    )
                    winreg.SetValueEx(key, 'Path', 0, winreg.REG_EXPAND_SZ, new_path)
                    winreg.CloseKey(key)
                    added.append(path_stripped)
                    current_path = new_path

            if added:
                self.broadcast_env_change()

            return added, skipped

        except Exception as e:
            self.log(f'[ERROR] Failed to add to PATH: {str(e)}')
            return [], []

    def set_environment_variable(self, name: str, value: str) -> bool:
        """设置系统环境变量"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )

            winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            winreg.CloseKey(key)

            self.broadcast_env_change()
            return True

        except Exception as e:
            self.log(f'[ERROR] Failed to set {name}: {str(e)}')
            return False

    def set_user_variable(self, name: str, value: str) -> bool:
        """设置用户环境变量"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Environment',
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )

            winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            winreg.CloseKey(key)

            self.broadcast_env_change()
            return True

        except Exception as e:
            self.log(f'[ERROR] Failed to set user var {name}: {str(e)}')
            return False

    def broadcast_env_change(self):
        """广播环境变量变更"""
        try:
            winreg.SendMessage(
                winreg.HWND_BROADCAST,
                winreg.WM_SETTINGCHANGE,
                0,
                'Environment'
            )
        except:
            pass

    def run(self) -> dict:
        """执行环境变量设置"""
        results = {
            'success': False,
            'path_added': 0,
            'path_skipped': 0,
            'vars_set': 0,
            'message': '',
            'errors': []
        }

        self.log('=' * 60)
        self.log('Environment Variables Setup')
        self.log('=' * 60)

        # 1. 解析配置
        self.log('\n[1] Parsing config...')
        if not self.parse_config():
            results['errors'] = self.log_lines
            return results

        self.log(f'    PATH entries: {len(self.path_entries)}')
        self.log(f'    PythonPath: {"configured" if self.pythonpath_value else "not set"}')
        self.log(f'    UserVars: {len(self.user_vars)}')

        # 2. 设置 PATH
        if self.path_entries:
            self.log('\n[2] Adding to PATH...')
            added, skipped = self.add_to_system_path(self.path_entries)
            results['path_added'] = len(added)
            results['path_skipped'] = len(skipped)

            for p in added:
                self.log(f'    [OK] Added: {p}')

            for p in skipped:
                self.log(f'    [SKIP] Already in PATH: {p}')

        # 3. 设置 PythonPath
        if self.pythonpath_value:
            self.log('\n[3] Creating PythonPath variable...')
            if self.set_environment_variable('PythonPath', self.pythonpath_value):
                self.log(f'    [OK] PythonPath = {self.pythonpath_value}')
                results['vars_set'] += 1
            else:
                self.log(f'    [FAIL] PythonPath')

        # 4. 设置用户变量
        if self.user_vars:
            self.log('\n[4] Setting User Variables...')
            for var_name, var_value in self.user_vars.items():
                if self.set_user_variable(var_name, var_value):
                    self.log(f'    [OK] {var_name} = {var_value}')
                    results['vars_set'] += 1
                else:
                    self.log(f'    [FAIL] {var_name}')

        results['success'] = True
        results['message'] = (
            f'PATH added: {results["path_added"]}, '
            f'PATH skipped: {results["path_skipped"]}, '
            f'Vars set: {results["vars_set"]}'
        )

        return results


def main():
    print('=' * 60)
    print('Environment Variables Setup')
    print('=' * 60)
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.txt')

    setup = EnvSetup(config_path)
    results = setup.run()

    print()
    print('=' * 60)
    if results['success']:
        print('[SUCCESS] Environment variables configured')
    else:
        print('[FAILED]')
    print(f'{results["message"]}')
    print('=' * 60)

    return 0 if results['success'] else 1


if __name__ == '__main__':
    exit(main())