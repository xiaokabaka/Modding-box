import re
import subprocess
import sys

#连接
while True:
    print('1.有线连接    2.无线连接    q.退出')
    link_input = input('请输入序号：')

    #有线
    if link_input == '1':

        # 模拟用户输入，实际使用时 link_input 应由 input() 获取
        # link_input = input("选择连接方式...")

            def select_usb_device_interactively():
                """
                1. 列出所有在线的 USB 设备。
                2. 让用户选择。
                3. 对选中的设备进行详细信息验证（模拟连接确认）。
                """
                devices = []

                # --- 第一步：获取设备列表 ---
                try:
                    # 检查 ADB 是否可用
                    result = subprocess.run(
                        ['adb', 'devices', '-l'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    # 检查命令是否启动失败 (例如 adb 程序被删除)
                    if result.returncode != 0:
                        print(f" ADB 服务异常，返回码: {result.returncode}")
                        print(f"   详细错误: {result.stderr}")
                        return None

                    lines = result.stdout.strip().splitlines()
                    header_skipped = False

                    for line in lines:
                        if not header_skipped:
                            if 'List of devices' in line:
                                header_skipped = True
                            continue

                        line = line.strip()
                        if not line:
                            continue

                        # 解析设备行
                        parts = line.split()
                        # 确保有足够的列，并且状态是 'device'
                        if len(parts) < 2 or parts[-1] != 'device':
                            continue

                        serial = parts[0]

                        # --- 第二步：尝试获取详细型号 (这一步相当于简单的“连接测试”) ---
                        try:
                            model_result = subprocess.run(
                                ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.model'],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            # 如果 shell 命令执行成功
                            if model_result.returncode == 0:
                                model = model_result.stdout.strip()
                            else:
                                model = "型号获取失败 (命令返回非0)"


                        except subprocess.TimeoutExpired:
                            model = "型号获取超时 (设备无响应)"

                        except Exception as e:
                            model = f"获取型号错误: {str(e)}"


                        devices.append((serial, model))

                except FileNotFoundError:
                    print("   错误：未找到 ADB 程序。")
                    print("   请确保已安装 Android SDK Platform Tools 并配置到系统环境变量 PATH 中。")
                    return None
                except subprocess.TimeoutExpired:
                    print("   错误：获取设备列表超时。")
                    print("   请检查 USB 连接是否稳定，或 ADB 服务是否卡死。")
                    return None
                except Exception as e:
                    print(f" 错误：发生未知错误 - {e}")
                    return None

                # --- 第三步：处理结果 ---
                if not devices:
                    print("  没有检测到任何在线的 USB 设备。")
                    print("  请检查：1. 数据线是否插好 2. 手机是否开启 USB 调试 3. 手机是否弹出授权窗口")
                    return None

                # --- 第四步：用户交互选择 ---
                print(f"\n 检测到 {len(devices)} 台设备，请选择：")
                for idx, (serial, model) in enumerate(devices):
                    print(f"  {idx + 1}. {serial} | 状态: {model}")

                while True:
                    try:
                        choice = input(f"\n请输入编号 (1-{len(devices)}) 选择设备，或输入 'q' 退出: ")
                        if choice.lower() == 'q':
                            return None

                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(devices):
                            selected_serial = devices[choice_idx][0]

                            # 这里可以模拟一个最终的“连接成功”确认
                            # 实际上上面已经连通了，这里为了演示提示逻辑
                            print(f"\n{'=' * 50}")
                            print(f"   连接成功！")
                            print(f"   设备序列号: {selected_serial}")
                            print(f"   状态: 已就绪，可以开始操作。")
                            print(f"{'=' * 50}\n")

                            return selected_serial
                        else:
                            print(f" 编号超出范围，请输入 1 到 {len(devices)} 之间的数字。")

                    except ValueError:
                        print(" 请输入有效的数字编号。")
                    except KeyboardInterrupt:
                        print("\n\n操作已取消。")
                        return None


            # --- 调用函数 ---
            device_serial = select_usb_device_interactively()

            if device_serial:
                print(f"脚本：你最终选择了设备 {device_serial}")
                break
            else:
                continue
                # sys.exit(1) # 如果你想在这里直接退出程序，可以取消注释这行


#无线
    elif link_input == '2':

        def is_adb_device_connected(ip, port):
            """
            检查指定 IP 和端口的设备是否已通过 ADB 连接且状态正常。
            """
            target_device = f"{ip}:{port}"

            try:
                result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, check=True)
                output = result.stdout

                # 检查输出中是否有 "ip:port    device"
                pattern = rf"{re.escape(target_device)}\s+device"

                if re.search(pattern, output):
                    return True
                else:
                    # 检查是否是 "unauthorized"
                    if target_device in output:
                        if "unauthorized" in output:
                            print("⚠ 设备未授权。请在手机上确认 RSA 密钥指纹！")
                        elif "offline" in output:
                            print("设备状态: offline")
                    return False

            except Exception as e:
                print(f"无法获取设备列表: {e}")
                return False


        def main():
            print('''                            ''')

            while True:
                # --- 步骤 1: 获取用户输入 ---
                print("\n" + "-" * 30)
                ip_input = input("请输入设备 IP 地址 (例如 192.168.1.100): ").strip()

                # 简单的输入验证（检查是否包含点号，防止完全乱输）
                if not ip_input or '.' not in ip_input:
                    print(" 输入无效，请输入正确的 IP 地址格式。")
                    continue

                # 端口通常默认是 5555，也可以让用户输入
                port_input = input(" 请输入端口号 (默认 5555，直接回车使用默认): ").strip()
                if not port_input:
                    port_input = "5555"

                target = f"{ip_input}:{port_input}"
                print(" 尝试连接到: {target}")

                # --- 步骤 2: 执行连接命令 ---
                try:
                    # 运行 adb connect
                    result = subprocess.run(['adb', 'connect', target], capture_output=True, text=True)
                    print(result.stdout)  # 通常会输出 connected to ... 或者 already connected

                    # --- 步骤 3: 判断是否真的连接成功 ---
                    if is_adb_device_connected(ip_input, port_input):
                        print(f"\n连接成功！设备 {target} 已就绪。")
                        break  # 跳出循环，结束程序
                    else:
                        print(f'\n连接 {target} 失败或设备未授权。')
                        print("请检查网络、确保设备已开启无线调试，并尝试重新输入 IP。")

                except FileNotFoundError:
                    print("错误: 找不到 ADB 命令。请确保已安装 ADB 并配置到系统环境变量中。")
                    break
                except Exception as e:
                    print(f"发生未知错误: {e}")
                    # 不 break，继续循环让用户重试


        if __name__ == "__main__":
            main()
    elif link_input == 'q':
        sys.exit(1)


    #执行
while True: # 创建一个无限循环
    print('1. shizuku' + '   2.Dhizuku') #展示
    print('3. Gesture' + '  4. 冰箱')
    print('5. 小黑屋' + '    6. 黑域')
    print('7. 空调狗' + '    8.绿色守护')
    print('q. 退出')

    user_input = input('请输入序号：')
    #shizuku
    if user_input == '1':
        subprocess.run("adb shell /data/app/moe.shizuku.privileged.api-SApnydInF-GjyokGBQOufA==/lib/arm64/libshizuku.so", shell=True)
    #dhizuku
    elif user_input == '2':
        while True:
            dhizuku_input = input('是否继续(y/n)：')   #判断是否继续
            if dhizuku_input == 'y':
                subprocess.run("adb shell dpm set-device-owner com.rosan.dhizuku/.server.DhizukuDAReceiver", shell=True)
            elif dhizuku_input == 'n':
                break
            else:
                print('无效操作')
    #Gesture
    elif user_input == '3':
        subprocess.run("adb -d shell sh /storage/emulated/0/Android/data/com.omarea.gesture/cache/up.sh ", shell=True)
    #冰箱
    elif user_input == '4':
        while True:
            print('1. 普通ADB模式    2. 设备管理员模式    q.返回')
            icebox_input = input('请输入序号：')
            if icebox_input == '1':
                subprocess.run('adb shell sh /sdcard/Android/data/com.catchingnow.icebox/files/start.sh', shell=True)
            elif icebox_input == '2':
                while True:
                    icebox_input = input('是否继续(y/n)：')
                    if icebox_input == 'y':
                        subprocess.run('adb shell dpm set-device-owner com.catchingnow.icebox/.receiver.DPMReceiver', shell=True)
                    elif icebox_input == 'n':
                        break
                    else:
                        print('无效操作')
            elif icebox_input == 'q':
                break
            else:
                print('无效操作')
    #小黑屋
    elif user_input == '5':
        while True:
            print('1. 麦克斯韦妖模式    2. 设备管理员模式    q.返回')
            stopapp_input = input('请输入序号：')
            if stopapp_input == '1':
                subprocess.run('adb shell sh /sdcard/Android/data/web1n.stopapp/files/demon.sh', shell=True)
            elif stopapp_input == '2':
                while True:
                    stopapp_input = input('是否继续(y/n)：')
                    if stopapp_input == 'y':
                        subprocess.run('adb shell dpm set-device-owner web1n.stopapp/.receiver.AdminReceiver', shell=True)
                    elif stopapp_input == 'n':
                        break
                    else:
                        print('无效操作')
            elif stopapp_input == 'q':
                break
            else:
                print('无效操作')
    #黑域
    elif user_input == '6':
        subprocess.run('adb shell sh /data/data/me.piebridge.brevent/brevent.sh', shell=True)
    #空调狗
    elif user_input == '7':
        while True:
            airfrozen_input = input('是否继续(y/n)：')
            if airfrozen_input == 'y':
                subprocess.run('adb shell dpm set-device-owner me.yourbay.airfrozen/.main.core.mgmt.MDeviceAdminReceiver', shell=True)
            elif airfrozen_input == 'n':
                break
            else:
                print('无效操作')
    #绿色守护
    elif user_input == '8':
        while True:
            greenify_input = input('是否继续(y/n)：')
            if greenify_input == 'y':
                subprocess.run('adb -d shell pm grant com.oasisfeng.greenify android.permission.DUMP', shell=True)
                subprocess.run('adb -d shell pm grant com.oasisfeng.greenify android.permission.READ_LOGS', shell=True)
                subprocess.run('adb -d shell pm grant com.oasisfeng.greenify android.permission.WRITE_SECURE_SETTINGS', shell=True)
                subprocess.run('adb -d shell am force-stop com.oasisfeng.greenify', shell=True)
            elif greenify_input == 'n':
                break
            else:
                print('无效操作')
                continue
    else:
        print('无效操作')
        continue
   
