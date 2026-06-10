"""
Batch Installer - 安装脚本
自动扫描 packages 文件夹，执行安装并生成结果
"""

import os
import sys
import subprocess
import shutil
import re
from datetime import datetime
from typing import List, Dict, Optional


class BatchInstaller:
    """批量安装器"""

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.packages_dir = os.path.join(self.script_dir, 'packages')
        self.results_file = os.path.join(self.script_dir, 'install_results.txt')
        self.log_lines = []
        self.errors = []

    def log(self, message: str):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{timestamp}] {message}'
        print(line)
        self.log_lines.append(line)

    def find_installer(self, package_path: str) -> Optional[str]:
        """查找安装包文件"""
        if not os.path.exists(package_path):
            return None

        extensions = ['.exe', '.msi']
        for item in os.listdir(package_path):
            item_path = os.path.join(package_path, item)
            if os.path.isfile(item_path):
                if any(item.lower().endswith(ext) for ext in extensions):
                    return item_path
        return None

    def get_installed_path_from_registry(self, software_name: str) -> Optional[str]:
        """从注册表查找已安装软件的路径"""
        try:
            import winreg

            # 常见软件的注册表位置
            reg_paths = [
                r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
            ]

            for reg_path in reg_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ)
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey_path = f'{reg_path}\\{subkey_name}'
                            subkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path, 0, winreg.KEY_READ)

                            try:
                                name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                                install_location, _ = winreg.QueryValueEx(subkey, 'InstallLocation')

                                if name and software_name.lower() in name.lower():
                                    if install_location and os.path.exists(install_location):
                                        return install_location
                            except:
                                pass

                            winreg.CloseKey(subkey)
                        except:
                            break
                        i += 1
                    winreg.CloseKey(key)
                except:
                    continue
        except:
            pass
        return None

    def run_installer(self, installer_path: str, software_name: str) -> tuple:
        """运行安装程序"""
        try:
            cmd = f'"{installer_path}" /S'
            self.log(f'Running: {os.path.basename(installer_path)}')

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600 # 10分钟超时
            )

            if result.returncode == 0:
                # 尝试从注册表获取安装路径
                installed_path = self.get_installed_path_from_registry(software_name)
                if installed_path:
                    return True, installed_path
                return True, 'Installed (path unknown)'
            else:
                return False, f'Install failed with code {result.returncode}'

        except subprocess.TimeoutExpired:
            return False, 'Install timeout'
        except Exception as e:
            return False, f'Error: {str(e)}'

    def save_results(self, results: List[dict]):
        """保存安装结果"""
        with open(self.results_file, 'w', encoding='utf-8') as f:
            f.write('=' * 60 + '\n')
            f.write('Installation Results\n')
            f.write('=' * 60 + '\n')
            f.write(f'Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'Total: {len(results)} packages\n')
            f.write('=' * 60 + '\n\n')

            for r in results:
                f.write(f'[{r["name"]}]\n')
                f.write(f'Source: {r["source"]}\n')
                f.write(f'Status: {r["status"]}\n')
                f.write(f'InstallPath: {r["install_path"]}\n')
                f.write('\n')

            f.write('=' * 60 + '\n')
            f.write('End of Results\n')
            f.write('=' * 60 + '\n')

    def run(self) -> dict:
        """执行安装流程"""
        results = {
            'success': False,
            'packages_found': 0,
            'packages_installed': 0,
            'packages_path_only': 0,
            'packages_failed': 0,
            'message': '',
            'errors': []
        }

        self.log('=' * 60)
        self.log('Batch Installer Started')
        self.log('=' * 60)

        # 1. 检查 packages 文件夹
        if not os.path.exists(self.packages_dir):
            self.errors.append(f'[ERROR] packages folder not found: {self.packages_dir}')
            results['errors'] = self.errors
            return results

        # 2. 扫描所有软件包
        self.log('\n[1] Scanning packages folder...')
        packages = []

        for item in os.listdir(self.packages_dir):
            item_path = os.path.join(self.packages_dir, item)
            if os.path.isdir(item_path):
                packages.append({
                    'name': item,
                    'path': item_path,
                    'installer': self.find_installer(item_path)
                })

        packages.sort(key=lambda x: x['name'])

        if not packages:
            self.errors.append('[ERROR] No packages found in packages folder')
            results['errors'] = self.errors
            return results

        self.log(f'    Found {len(packages)} packages:')
        for pkg in packages:
            status = 'installer' if pkg['installer'] else 'path only'
            self.log(f'      - {pkg["name"]} [{status}]')

        results['packages_found'] = len(packages)

        # 3. 安装每个包
        install_results = []

        self.log('\n[2] Installing packages...')

        for i, pkg in enumerate(packages, 1):
            self.log(f'\n--- Package {i}/{len(packages)}: {pkg["name"]} ---')

            result = {
                'name': pkg['name'],
                'source': pkg['path'],
                'status': 'Unknown',
                'install_path': ''
            }

            if pkg['installer']:
                # 有安装包，运行安装
                self.log(f'    Found installer: {os.path.basename(pkg["installer"])}')
                self.log(f'    Running installation...')

                ok, msg = self.run_installer(pkg['installer'], pkg['name'])

                if ok:
                    result['status'] = 'Installed'
                    result['install_path'] = msg
                    results['packages_installed'] += 1
                    self.log(f'    [OK] Installed to: {msg}')
                else:
                    result['status'] = 'Failed'
                    result['install_path'] = msg
                    results['packages_failed'] += 1
                    self.log(f'    [FAIL] {msg}')
            else:
                # 没有安装包，记录路径
                result['status'] = 'Path Only'
                result['install_path'] = pkg['path']
                results['packages_path_only'] += 1
                self.log(f'    [PATH] No installer found, using folder path')
                self.log(f'    Path: {pkg["path"]}')

            install_results.append(result)

        # 4. 保存结果
        self.log('\n[3] Saving results...')
        self.save_results(install_results)
        self.log(f'    Results saved to: {self.results_file}')

        # 5. 完成
        results['success'] = results['packages_failed'] == 0
        results['message'] = (
            f'Total: {results["packages_found"]}, '
            f'Installed: {results["packages_installed"]}, '
            f'PathOnly: {results["packages_path_only"]}, '
            f'Failed: {results["packages_failed"]}'
        )

        return results


def main():
    print('=' * 60)
    print('Batch Installer')
    print('=' * 60)
    print()

    installer = BatchInstaller()
    results = installer.run()

    print()
    print('=' * 60)
    if results['success']:
        print('[SUCCESS] Installation completed')
    else:
        print('[WARNING] Completed with some failures')
    print(f'{results["message"]}')
    print('=' * 60)

    return 0 if results['success'] else 1


if __name__ == '__main__':
    exit(main())