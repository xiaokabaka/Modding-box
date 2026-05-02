import re
import subprocess
import sys
import time
from pathlib import Path
def run_adb_command(args, timeout=10, adb_path=None):
    """
    统一执行 ADB 命令的函数
    """
    try:
        if adb_path is None:
            cmd = ['adb'] + args
        else:
            cmd = [adb_path] + args
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out."
    except FileNotFoundError:
        return -2, "", f"ADB not found. Please ensure ADB is in PATH or provide correct path."
    except Exception as e:
        return -3, "", f"An error occurred: {e}"


def confirm_action(prompt="是否继续(y/n)："):
    """
    通用的 y/n 确认函数
    """
    while True:
        try:
            choice = input(prompt).strip().lower()
            if choice == 'y':
                return True
            elif choice == 'n':
                return False
            else:
                print('无效操作，请输入 y 或 n')
        except KeyboardInterrupt:
            print("\n操作已取消")
            return False


def validate_ip_address(ip):
    """
    验证 IP 地址格式是否正确
    """
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    match = re.match(pattern, ip)
    if not match:
        return False
    
    for group in match.groups():
        if int(group) > 255:
            return False
    return True


def validate_port(port_str):
    """
    验证端口号是否在有效范围内
    """
    try:
        port = int(port_str)
        return 1 <= port <= 65535
    except ValueError:
        return False


# 主程序
connected = False
device_serial = None
local_adb_path = None

def find_adb_executable(start_path=None):
    """
    在指定起始路径及其子目录中查找 adb 可执行文件。
    默认从脚本所在目录开始查找。
    """
    if start_path is None:
        start_path = Path(__file__).resolve().parent
    else:
        start_path = Path(start_path).resolve()

    search_paths = [start_path, start_path / "platform-tools"]

    for base_dir in search_paths:
        possible_files = ["adb", "adb.exe"]
        for file_name in possible_files:
            adb_path = base_dir / file_name
            if adb_path.is_file():
                print(f"  > 在 '{base_dir}' 中找到 ADB 程序: {adb_path.name}")
                return str(adb_path.resolve())

    print(f"  [错误] 未能在 '{start_path}' 或其 'platform-tools' 子目录中找到 'adb' 或 'adb.exe' 文件。")
    print("  请确保 ADB 文件已放置在脚本所在目录或其 'platform-tools' 文件夹内。")
    return None


def check_device_connected(adb_path=None):
    """
    检查是否有设备已连接
    """
    ret_code, output, error = run_adb_command(['devices'], timeout=5, adb_path=adb_path)
    
    if ret_code != 0:
        return False, []
    
    devices = []
    lines = output.strip().splitlines()
    
    for line in lines[1:]:  # 跳过标题行
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        if len(parts) >= 2 and parts[-1] == 'device':
            devices.append(parts[0])
    
    return len(devices) > 0, devices


# 首先查找 ADB 程序
print("正在初始化 ADB...")
local_adb_path = find_adb_executable()

if local_adb_path:
    print(f"\n使用 ADB: {local_adb_path}\n")
else:
    print("\n[错误] 未找到 ADB 程序，脚本无法继续执行。")
    sys.exit(1)

# 检查是否有设备已连接
print("检查设备连接状态...")
has_device, connected_devices = check_device_connected(local_adb_path)

if has_device:
    print(f"\n检测到 {len(connected_devices)} 个已连接的设备:")
    for device in connected_devices:
        print(f"  - {device}")
    
    try:
        use_existing = input("\n是否使用已连接的设备？(y/n，输入 n 重新连接): ").strip().lower()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    
    if use_existing == 'y':
        if len(connected_devices) == 1:
            device_serial = connected_devices[0]
            connected = True
            print(f"\n使用设备: {device_serial}")
        else:
            # 多个设备时让用户选择
            print("\n请选择要使用的设备:")
            for idx, device in enumerate(connected_devices):
                print(f"  [{idx + 1}] {device}")
            
            while True:
                try:
                    choice = input(f"\n请输入编号 (1-{len(connected_devices)}): ").strip()
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(connected_devices):
                        device_serial = connected_devices[choice_idx]
                        connected = True
                        print(f"\n使用设备: {device_serial}")
                        break
                    else:
                        print(f" [错误] 编号超出范围，请输入 1 到 {len(connected_devices)} 之间的数字。")
                except ValueError:
                    print(" [错误] 请输入有效的数字编号。")
                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    sys.exit(0)
    else:
        print("\n将进入设备连接流程...\n")
else:
    print("\n未检测到已连接的设备，请进行设备连接。\n")

#连接
while not connected:
    print('1.有线连接    2.无线连接    q.退出')
    try:
        link_input = input('请输入序号：').strip()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)

    #有线
    if link_input == '1':
        print("\n正在检测设备连接状态...")
        has_device, detected_devices = check_device_connected(local_adb_path)
        
        if has_device:
            print(f"\n检测到 {len(detected_devices)} 个已连接的设备:")
            
            # 获取设备详细信息
            devices_with_info = []
            for serial in detected_devices:
                print(f"  正在获取设备 {serial} 的信息...")
                model_ret_code, model_output, _ = run_adb_command(
                    ['-s', serial, 'shell', 'getprop', 'ro.product.model'], 
                    timeout=5, 
                    adb_path=local_adb_path
                )
                if model_ret_code == 0:
                    model = model_output.strip()
                else:
                    model = "未知型号"
                devices_with_info.append((serial, model))
                print(f"    - {serial} | 型号: {model}")
            
            # 让用户选择设备
            if len(devices_with_info) == 1:
                try:
                    use_single = input("\n只检测到一个设备，是否使用？(y/n): ").strip().lower()
                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    continue
                
                if use_single == 'y':
                    device_serial = devices_with_info[0][0]
                    connected = True
                    print(f"\n使用设备: {device_serial}")
                    continue
                else:
                    print("将重新扫描设备...")
            
            # 多个设备时让用户选择
            print("\n请选择要使用的设备:")
            for idx, (serial, model) in enumerate(devices_with_info):
                print(f"  [{idx + 1}] {serial} | 型号: {model}")
            
            while True:
                try:
                    choice = input(f"\n请输入编号 (1-{len(devices_with_info)})，或输入 'r' 重新扫描，'q' 退出: ").strip().lower()
                    if choice == 'q':
                        sys.exit(0)
                    elif choice == 'r':
                        break  # 跳出选择循环，重新扫描
                    
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(devices_with_info):
                        selected_serial = devices_with_info[choice_idx][0]
                        
                        # 验证设备连接
                        confirm_ret_code, confirm_out, _ = run_adb_command(
                            ['-s', selected_serial, 'shell', 'echo', 'connection_ok'], 
                            timeout=5, 
                            adb_path=local_adb_path
                        )
                        if confirm_ret_code == 0 and confirm_out.strip() == 'connection_ok':
                            device_serial = selected_serial
                            connected = True
                            print(f"\n{'=' * 50}")
                            print(f"   连接成功！")
                            print(f"   设备序列号: {device_serial}")
                            print(f"   型号: {devices_with_info[choice_idx][1]}")
                            print(f"   状态: 已就绪，可以开始操作。")
                            print(f"{'=' * 50}\n")
                            break
                        else:
                            print(f"\n[警告] 设备 {selected_serial} 验证失败，请重试。")
                    else:
                        print(f" [错误] 编号超出范围，请输入 1 到 {len(devices_with_info)} 之间的数字。")
                except ValueError:
                    print(" [错误] 请输入有效的数字编号。")
                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    continue
            
            if connected:
                continue
        else:
            print("\n未检测到任何已连接的设备。")
            print("\n--- 请按以下步骤逐一排查 ---")
            print("  1. 检查数据线：更换一根数据线，确保它是全功能线（支持数据传输，不仅仅是充电）。")
            print("  2. 检查手机 USB 调试：")
            print("     - 确认手机已开启 '开发者选项' 和 'USB 调试'。")
            print("     - 如果之前授权过，在手机上进入 '开发者选项' -> '撤销 USB 调试授权'，然后重新连接。")
            print("  3. 检查 USB 连接模式：")
            print("     - 连接电脑后，下拉手机通知栏，查看 'USB 选项' 或 '正在充电'。")
            print("     - 点击并选择 '文件传输 (MTP)' 或 '传输' 模式。")
            print("  4. 检查电脑驱动程序（Windows 用户特别注意）：")
            print("     - 访问手机制造商官网，下载并安装其官方 USB 驱动程序。")
            print("       (例如：小米助手, 华为手机助手, Samsung USB Driver, Google USB Driver)")
            print("     - 或者在 '设备管理器' 中查看是否有带感叹号的未知设备，并尝试更新驱动。")
            print("------------------------------\n")
            
            try:
                retry = input("是否重新检测？(y/n): ").strip().lower()
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                continue
            
            if retry != 'y':
                continue

    #无线
    elif link_input == '2':

        def is_adb_device_connected(ip, port, adb_path=None):
            """
            检查指定 IP 和端口的设备是否已通过 ADB 连接且状态正常。
            """
            target_device = f"{ip}:{port}"

            try:
                result = subprocess.run([adb_path or 'adb', 'devices'], capture_output=True, text=True, check=True)
                output = result.stdout

                pattern = rf"{re.escape(target_device)}\s+device"

                if re.search(pattern, output):
                    return True
                else:
                    if target_device in output:
                        if "unauthorized" in output:
                            print("⚠ 设备未授权。请在手机上确认 RSA 密钥指纹！")
                        elif "offline" in output:
                            print("设备状态: offline")
                    return False

            except Exception as e:
                print(f"无法获取设备列表: {e}")
                return False


        def wireless_connect():
            print('''                            ''')

            while True:
                try:
                    print("\n" + "-" * 30)
                    ip_input = input("请输入设备 IP 地址 (例如 192.168.1.100): ").strip()

                    if not validate_ip_address(ip_input):
                        print(" 输入无效，请输入正确的 IP 地址格式。")
                        continue

                    port_input = input(" 请输入端口号 (默认 5555，直接回车使用默认): ").strip()
                    if not port_input:
                        port_input = "5555"
                    
                    if not validate_port(port_input):
                        print(" 端口号无效，请输入 1-65535 之间的数字。")
                        continue

                    target = f"{ip_input}:{port_input}"
                    print(f" 尝试连接到: {target}")

                    result = subprocess.run([local_adb_path or 'adb', 'connect', target], capture_output=True, text=True)
                    print(result.stdout)

                    if is_adb_device_connected(ip_input, port_input, local_adb_path):
                        print(f"\n连接成功！设备 {target} 已就绪。")
                        return target
                    else:
                        print(f'\n连接 {target} 失败或设备未授权。')
                        print("请检查网络、确保设备已开启无线调试，并尝试重新输入 IP。")

                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    return None
                except FileNotFoundError:
                    print("错误: 找不到 ADB 命令。请确保已安装 ADB 并配置到系统环境变量中。")
                    return None
                except Exception as e:
                    print(f"发生未知错误: {e}")
                    return None


        result = wireless_connect()
        if result:
            connected = True
        else:
            continue
    elif link_input == 'q':
        sys.exit(0)
    else:
        print('无效操作')
        continue

#执行
while connected:
    print('1. shizuku' + '   2.Dhizuku')
    print('3. Gesture' + '  4. 冰箱')
    print('5. 小黑屋' + '    6. 黑域')
    print('7. 空调狗' + '    8.绿色守护')
    print('a. 重新连接' + '   b. 退出')

    try:
        user_input = input('请输入序号：').strip()
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        break
    
    #重新连接
    if user_input == 'a':
        print("\n正在断开当前设备连接...")
        connected = False
        device_serial = None
        
        # 重新进入设备连接流程
        while not connected:
            print('\n请选择连接方式：')
            print('1.有线连接    2.无线连接    q.返回主菜单')
            try:
                link_input = input('请输入序号：').strip()
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                break
            
            if link_input == '1':
                print("\n正在检测设备连接状态...")
                has_device, detected_devices = check_device_connected(local_adb_path)
                
                if has_device:
                    print(f"\n检测到 {len(detected_devices)} 个已连接的设备:")
                    
                    # 获取设备详细信息
                    devices_with_info = []
                    for serial in detected_devices:
                        print(f"  正在获取设备 {serial} 的信息...")
                        model_ret_code, model_output, _ = run_adb_command(
                            ['-s', serial, 'shell', 'getprop', 'ro.product.model'], 
                            timeout=5, 
                            adb_path=local_adb_path
                        )
                        if model_ret_code == 0:
                            model = model_output.strip()
                        else:
                            model = "未知型号"
                        devices_with_info.append((serial, model))
                        print(f"    - {serial} | 型号: {model}")
                    
                    # 让用户选择设备
                    if len(devices_with_info) == 1:
                        try:
                            use_single = input("\n只检测到一个设备，是否使用？(y/n): ").strip().lower()
                        except KeyboardInterrupt:
                            print("\n\n操作已取消")
                            continue
                        
                        if use_single == 'y':
                            device_serial = devices_with_info[0][0]
                            connected = True
                            print(f"\n使用设备: {device_serial}")
                            break
                        else:
                            print("将重新扫描设备...")
                    
                    # 多个设备时让用户选择
                    print("\n请选择要使用的设备:")
                    for idx, (serial, model) in enumerate(devices_with_info):
                        print(f"  [{idx + 1}] {serial} | 型号: {model}")
                    
                    while True:
                        try:
                            choice = input(f"\n请输入编号 (1-{len(devices_with_info)})，或输入 'r' 重新扫描，'q' 退出: ").strip().lower()
                            if choice == 'q':
                                break
                            elif choice == 'r':
                                break  # 跳出选择循环，重新扫描
                            
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(devices_with_info):
                                selected_serial = devices_with_info[choice_idx][0]
                                
                                # 验证设备连接
                                confirm_ret_code, confirm_out, _ = run_adb_command(
                                    ['-s', selected_serial, 'shell', 'echo', 'connection_ok'], 
                                    timeout=5, 
                                    adb_path=local_adb_path
                                )
                                if confirm_ret_code == 0 and confirm_out.strip() == 'connection_ok':
                                    device_serial = selected_serial
                                    connected = True
                                    print(f"\n{'=' * 50}")
                                    print(f"   连接成功！")
                                    print(f"   设备序列号: {device_serial}")
                                    print(f"   型号: {devices_with_info[choice_idx][1]}")
                                    print(f"   状态: 已就绪，可以开始操作。")
                                    print(f"{'=' * 50}\n")
                                    break
                                else:
                                    print(f"\n[警告] 设备 {selected_serial} 验证失败，请重试。")
                            else:
                                print(f" [错误] 编号超出范围，请输入 1 到 {len(devices_with_info)} 之间的数字。")
                        except ValueError:
                            print(" [错误] 请输入有效的数字编号。")
                        except KeyboardInterrupt:
                            print("\n\n操作已取消")
                            continue
                    
                    if connected:
                        break
                else:
                    print("\n未检测到任何已连接的设备。")
                    print("\n--- 请按以下步骤逐一排查 ---")
                    print("  1. 检查数据线：更换一根数据线，确保它是全功能线（支持数据传输，不仅仅是充电）。")
                    print("  2. 检查手机 USB 调试：")
                    print("     - 确认手机已开启 '开发者选项' 和 'USB 调试'。")
                    print("     - 如果之前授权过，在手机上进入 '开发者选项' -> '撤销 USB 调试授权'，然后重新连接。")
                    print("  3. 检查 USB 连接模式：")
                    print("     - 连接电脑后，下拉手机通知栏，查看 'USB 选项' 或 '正在充电'。")
                    print("     - 点击并选择 '文件传输 (MTP)' 或 '传输' 模式。")
                    print("  4. 检查电脑驱动程序（Windows 用户特别注意）：")
                    print("     - 访问手机制造商官网，下载并安装其官方 USB 驱动程序。")
                    print("       (例如：小米助手, 华为手机助手, Samsung USB Driver, Google USB Driver)")
                    print("------------------------------\n")
                    
                    try:
                        retry = input("是否重新检测？(y/n): ").strip().lower()
                    except KeyboardInterrupt:
                        print("\n\n操作已取消")
                        continue
                    
                    if retry != 'y':
                        break
            
            elif link_input == '2':
                def is_adb_device_connected(ip, port, adb_path=None):
                    target_device = f"{ip}:{port}"
                    try:
                        result = subprocess.run([adb_path or 'adb', 'devices'], capture_output=True, text=True, check=True)
                        output = result.stdout
                        pattern = rf"{re.escape(target_device)}\s+device"
                        if re.search(pattern, output):
                            return True
                        else:
                            if target_device in output:
                                if "unauthorized" in output:
                                    print("⚠ 设备未授权。请在手机上确认 RSA 密钥指纹！")
                                elif "offline" in output:
                                    print("设备状态: offline")
                            return False
                    except Exception as e:
                        print(f"无法获取设备列表: {e}")
                        return False
                
                print("\n无线连接设置：")
                try:
                    ip_input = input("请输入设备 IP 地址 (例如 192.168.1.100): ").strip()
                    if not validate_ip_address(ip_input):
                        print(" 输入无效，请输入正确的 IP 地址格式。")
                        continue
                    
                    port_input = input(" 请输入端口号 (默认 5555，直接回车使用默认): ").strip()
                    if not port_input:
                        port_input = "5555"
                    
                    if not validate_port(port_input):
                        print(" 端口号无效，请输入 1-65535 之间的数字。")
                        continue
                    
                    target = f"{ip_input}:{port_input}"
                    print(f" 尝试连接到: {target}")
                    
                    result = subprocess.run([local_adb_path or 'adb', 'connect', target], capture_output=True, text=True)
                    print(result.stdout)
                    
                    if is_adb_device_connected(ip_input, port_input, local_adb_path):
                        print(f"\n连接成功！设备 {target} 已就绪。")
                        device_serial = target
                        connected = True
                        break
                    else:
                        print(f'\n连接 {target} 失败或设备未授权。')
                        print("请检查网络、确保设备已开启无线调试，并尝试重新输入 IP。")
                
                except KeyboardInterrupt:
                    print("\n\n操作已取消")
                    continue
            
            elif link_input == 'q':
                break
            else:
                print('无效操作')
                continue
        
        if not connected:
            print("\n返回主菜单")
            continue
    
    #shizuku
    if user_input == '1':
        ret_code, output, error = run_adb_command(
            ['shell', '/data/app/moe.shizuku.privileged.api-SApnydInF-GjyokGBQOufA==/lib/arm64/libshizuku.so'],
            adb_path=local_adb_path
        )
        if ret_code != 0:
            print(f"执行失败: {error}")
    
    #dhizuku
    elif user_input == '2':
        if confirm_action():
            ret_code, output, error = run_adb_command(
                ['shell', 'dpm', 'set-device-owner', 'com.rosan.dhizuku/.server.DhizukuDAReceiver'],
                adb_path=local_adb_path
            )
            if ret_code != 0:
                print(f"执行失败: {error}")
            else:
                print(output)
    
    #Gesture
    elif user_input == '3':
        ret_code, output, error = run_adb_command(
            ['-d', 'shell', 'sh', '/storage/emulated/0/Android/data/com.omarea.gesture/cache/up.sh'],
            adb_path=local_adb_path
        )
        if ret_code != 0:
            print(f"执行失败: {error}")
        else:
            print(output)
    
    #冰箱
    elif user_input == '4':
        while True:
            print('1. 普通ADB模式    2. 设备管理员模式    q.返回')
            try:
                icebox_input = input('请输入序号：').strip()
            except KeyboardInterrupt:
                print("\n操作已取消")
                break
            
            if icebox_input == '1':
                ret_code, output, error = run_adb_command(
                    ['shell', 'sh', '/sdcard/Android/data/com.catchingnow.icebox/files/start.sh'],
                    adb_path=local_adb_path
                )
                if ret_code != 0:
                    print(f"执行失败: {error}")
                else:
                    print(output)
            elif icebox_input == '2':
                if confirm_action():
                    ret_code, output, error = run_adb_command(
                        ['shell', 'dpm', 'set-device-owner', 'com.catchingnow.icebox/.receiver.DPMReceiver'],
                        adb_path=local_adb_path
                    )
                    if ret_code != 0:
                        print(f"执行失败: {error}")
                    else:
                        print(output)
            elif icebox_input == 'q':
                break
            else:
                print('无效操作')
    
    #小黑屋
    elif user_input == '5':
        while True:
            print('1. 麦克斯韦妖模式    2. 设备管理员模式    q.返回')
            try:
                stopapp_input = input('请输入序号：').strip()
            except KeyboardInterrupt:
                print("\n操作已取消")
                break
            
            if stopapp_input == '1':
                ret_code, output, error = run_adb_command(
                    ['shell', 'sh', '/sdcard/Android/data/web1n.stopapp/files/demon.sh'],
                    adb_path=local_adb_path
                )
                if ret_code != 0:
                    print(f"执行失败: {error}")
                else:
                    print(output)
            elif stopapp_input == '2':
                if confirm_action():
                    ret_code, output, error = run_adb_command(
                        ['shell', 'dpm', 'set-device-owner', 'web1n.stopapp/.receiver.AdminReceiver'],
                        adb_path=local_adb_path
                    )
                    if ret_code != 0:
                        print(f"执行失败: {error}")
                    else:
                        print(output)
            elif stopapp_input == 'q':
                break
            else:
                print('无效操作')
    
    #黑域
    elif user_input == '6':
        ret_code, output, error = run_adb_command(
            ['shell', 'sh', '/data/data/me.piebridge.brevent/brevent.sh'],
            adb_path=local_adb_path
        )
        if ret_code != 0:
            print(f"执行失败: {error}")
        else:
            print(output)
    
    #空调狗
    elif user_input == '7':
        if confirm_action():
            ret_code, output, error = run_adb_command(
                ['shell', 'dpm', 'set-device-owner', 'me.yourbay.airfrozen/.main.core.mgmt.MDeviceAdminReceiver'],
                adb_path=local_adb_path
            )
            if ret_code != 0:
                print(f"执行失败: {error}")
            else:
                print(output)
    
    #绿色守护
    elif user_input == '8':
        if confirm_action():
            permissions = [
                'android.permission.DUMP',
                'android.permission.READ_LOGS',
                'android.permission.WRITE_SECURE_SETTINGS'
            ]
            for perm in permissions:
                ret_code, output, error = run_adb_command(
                    ['-d', 'shell', 'pm', 'grant', 'com.oasisfeng.greenify', perm],
                    adb_path=local_adb_path
                )
                if ret_code != 0:
                    print(f"授予权限 {perm} 失败: {error}")
            
            ret_code, output, error = run_adb_command(
                ['-d', 'shell', 'am', 'force-stop', 'com.oasisfeng.greenify'],
                adb_path=local_adb_path
            )
            if ret_code != 0:
                print(f"停止应用失败: {error}")
    
    elif user_input == 'b':
        print("感谢使用，再见！")
        break
    else:
        print('无效操作')
        continue
