#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用 TCP 客户端
支持连接到 TCP 服务端，发送和接收消息
"""

import socket
import threading
import logging
import json
import time
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TCPClient:
    """通用 TCP 客户端类"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888, timeout: int = 10):
        """
        初始化 TCP 客户端
        
        Args:
            host: 服务端地址，默认 localhost
            port: 服务端端口，默认 8888
            timeout: 连接超时时间（秒），默认 10 秒
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client_socket: Optional[socket.socket] = None
        self.is_connected = False
        self.is_receiving = False
        self.receive_thread: Optional[threading.Thread] = None
        
    def connect(self) -> bool:
        """
        连接到服务端
        
        Returns:
            连接是否成功
        """
        try:
            # 创建 TCP socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(self.timeout)
            
            # 连接到服务端
            logger.info(f"正在连接到 {self.host}:{self.port}...")
            self.client_socket.connect((self.host, self.port))
            
            self.is_connected = True
            logger.info(f"成功连接到服务端 {self.host}:{self.port}")
            
            # 启动接收消息线程
            self._start_receiving()
            
            return True
            
        except socket.timeout:
            logger.error(f"连接超时: {self.host}:{self.port}")
            return False
        except ConnectionRefusedError:
            logger.error(f"连接被拒绝: {self.host}:{self.port}（服务端可能未启动）")
            return False
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
            
    def _start_receiving(self):
        """启动接收消息线程"""
        self.is_receiving = True
        self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
        self.receive_thread.start()
        
    def _receive_messages(self):
        """接收服务端消息（循环）"""
        while self.is_receiving and self.is_connected:
            try:
                # 接收数据
                data = self.client_socket.recv(4096)
                
                if not data:
                    # 服务端断开连接
                    logger.warning("服务端已断开连接")
                    self.is_connected = False
                    break
                
                # 解析接收到的数据
                try:
                    message = data.decode('utf-8')
                    self._handle_message(message)
                except UnicodeDecodeError:
                    logger.warning("无法解码服务端消息")
                    
            except socket.timeout:
                # 超时是正常的，继续接收
                continue
            except Exception as e:
                if self.is_receiving:
                    logger.error(f"接收消息时出错: {e}")
                break
                
    def _handle_message(self, message: str):
        """
        处理服务端消息（可根据需要自定义）
        
        Args:
            message: 服务端消息
        """
        try:
            # 尝试解析 JSON 格式
            msg_data = json.loads(message)
            msg_type = msg_data.get('type', 'unknown')
            
            if msg_type == 'welcome':
                logger.info(f"[服务端欢迎] {msg_data.get('message')}")
            elif msg_type == 'pong':
                logger.info(f"[PONG] {msg_data.get('message')}")
            elif msg_type == 'echo_response':
                logger.info(f"[回显] {msg_data.get('original_message')}")
            elif msg_type == 'error':
                logger.error(f"[错误] {msg_data.get('message')}")
            else:
                logger.info(f"[服务端] {json.dumps(msg_data, ensure_ascii=False, indent=2)}")
                
        except json.JSONDecodeError:
            # 非 JSON 格式
            logger.info(f"[服务端] {message}")
            
    def send_message(self, message: str) -> bool:
        """
        发送文本消息
        
        Args:
            message: 要发送的消息
            
        Returns:
            发送是否成功
        """
        if not self.is_connected:
            logger.error("未连接到服务端")
            return False
            
        try:
            self.client_socket.sendall(message.encode('utf-8'))
            logger.info(f"[发送] {message}")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.is_connected = False
            return False
            
    def send_json(self, data: dict) -> bool:
        """
        发送 JSON 格式消息
        
        Args:
            data: 要发送的数据字典
            
        Returns:
            发送是否成功
        """
        try:
            message = json.dumps(data, ensure_ascii=False)
            return self.send_message(message)
        except Exception as e:
            logger.error(f"序列化 JSON 失败: {e}")
            return False
            
    def ping(self) -> bool:
        """
        发送 ping 消息测试连接
        
        Returns:
            发送是否成功
        """
        return self.send_json({'type': 'ping'})
        
    def echo(self, message: str) -> bool:
        """
        发送 echo 消息
        
        Args:
            message: 要回显的消息
            
        Returns:
            发送是否成功
        """
        return self.send_json({
            'type': 'echo',
            'message': message
        })
        
    def disconnect(self):
        """断开连接"""
        logger.info("正在断开连接...")
        self.is_receiving = False
        self.is_connected = False
        
        # 等待接收线程结束
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2)
        
        # 关闭 socket
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
                
        logger.info("已断开连接")
        
    def is_alive(self) -> bool:
        """检查连接是否存活"""
        return self.is_connected


def interactive_mode(client: TCPClient):
    """交互模式"""
    print("\n" + "="*50)
    print("TCP 客户端交互模式")
    print("="*50)
    print("命令列表:")
    print("  ping              - 测试连接")
    print("  echo <消息>       - 回显消息")
    print("  send <消息>       - 发送文本消息")
    print("  json <JSON数据>   - 发送 JSON 消息")
    print("  quit/exit         - 退出")
    print("="*50 + "\n")
    
    while client.is_alive():
        try:
            user_input = input(">>> ").strip()
            
            if not user_input:
                continue
                
            # 解析命令
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if command in ['quit', 'exit']:
                break
            elif command == 'ping':
                client.ping()
            elif command == 'echo':
                if args:
                    client.echo(args)
                else:
                    print("用法: echo <消息>")
            elif command == 'send':
                if args:
                    client.send_message(args)
                else:
                    print("用法: send <消息>")
            elif command == 'json':
                if args:
                    try:
                        json_data = json.loads(args)
                        client.send_json(json_data)
                    except json.JSONDecodeError:
                        print("错误: 无效的 JSON 格式")
                else:
                    print("用法: json <JSON数据>")
            else:
                print(f"未知命令: {command}")
                print("输入 'help' 查看命令列表")
                
        except KeyboardInterrupt:
            print("\n")
            break
        except EOFError:
            break


def main():
    """主函数"""
    # 创建客户端实例
    client = TCPClient(host='localhost', port=8888, timeout=10)
    
    try:
        # 连接到服务端
        if client.connect():
            # 等待一下，接收欢迎消息
            time.sleep(0.5)
            
            # 进入交互模式
            interactive_mode(client)
        else:
            logger.error("无法连接到服务端")
            
    except KeyboardInterrupt:
        logger.info("\n接收到中断信号")
    finally:
        # 断开连接
        client.disconnect()


if __name__ == '__main__':
    main()
