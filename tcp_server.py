#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用 TCP 服务端
支持多客户端并发连接，使用线程池处理客户端请求
"""

import socket
import threading
import logging
import json
from datetime import datetime
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TCPServer:
    """通用 TCP 服务端类"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8888, max_connections: int = 5):
        """
        初始化 TCP 服务端
        
        Args:
            host: 监听地址，默认 0.0.0.0（所有网络接口）
            port: 监听端口，默认 8888
            max_connections: 最大连接数，默认 5
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.clients = []
        self.client_lock = threading.Lock()
        
    def start(self):
        """启动服务端"""
        try:
            # 创建 TCP socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 设置 socket 选项，允许地址重用
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            # 开始监听
            self.server_socket.listen(self.max_connections)
            
            self.is_running = True
            logger.info(f"服务端启动成功，监听 {self.host}:{self.port}")
            logger.info(f"最大连接数: {self.max_connections}")
            
            # 接受客户端连接
            self._accept_connections()
            
        except Exception as e:
            logger.error(f"服务端启动失败: {e}")
            self.stop()
            
    def _accept_connections(self):
        """接受客户端连接（循环）"""
        while self.is_running:
            try:
                # 接受新连接
                client_socket, client_address = self.server_socket.accept()
                logger.info(f"新客户端连接: {client_address}")
                
                # 为每个客户端创建独立线程
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
                # 记录客户端信息
                with self.client_lock:
                    self.clients.append({
                        'socket': client_socket,
                        'address': client_address,
                        'thread': client_thread,
                        'connected_at': datetime.now()
                    })
                    
            except OSError:
                # Socket 关闭时会抛出异常
                if not self.is_running:
                    break
            except Exception as e:
                logger.error(f"接受连接时出错: {e}")
                
    def _handle_client(self, client_socket: socket.socket, client_address: tuple):
        """
        处理单个客户端连接
        
        Args:
            client_socket: 客户端 socket
            client_address: 客户端地址
        """
        try:
            # 发送欢迎消息
            welcome_msg = {
                'type': 'welcome',
                'message': '欢迎连接到 TCP 服务端',
                'server_time': datetime.now().isoformat()
            }
            self._send_message(client_socket, welcome_msg)
            
            # 持续接收客户端消息
            while self.is_running:
                data = client_socket.recv(4096)
                
                if not data:
                    # 客户端断开连接
                    logger.info(f"客户端断开连接: {client_address}")
                    break
                
                # 解析接收到的数据
                try:
                    message = data.decode('utf-8')
                    logger.info(f"收到来自 {client_address} 的消息: {message}")
                    
                    # 处理消息并返回响应
                    response = self._process_message(message, client_address)
                    self._send_message(client_socket, response)
                    
                except UnicodeDecodeError:
                    logger.warning(f"无法解码来自 {client_address} 的消息")
                    error_response = {
                        'type': 'error',
                        'message': '消息格式错误，请使用 UTF-8 编码'
                    }
                    self._send_message(client_socket, error_response)
                    
        except Exception as e:
            logger.error(f"处理客户端 {client_address} 时出错: {e}")
            
        finally:
            # 关闭客户端连接
            self._close_client(client_socket, client_address)
            
    def _process_message(self, message: str, client_address: tuple) -> dict:
        """
        处理客户端消息（可根据需要自定义）
        
        Args:
            message: 客户端消息
            client_address: 客户端地址
            
        Returns:
            响应消息字典
        """
        # 尝试解析 JSON 格式消息
        try:
            msg_data = json.loads(message)
            msg_type = msg_data.get('type', 'unknown')
            
            if msg_type == 'ping':
                return {
                    'type': 'pong',
                    'message': '服务端在线',
                    'server_time': datetime.now().isoformat()
                }
            elif msg_type == 'echo':
                return {
                    'type': 'echo_response',
                    'original_message': msg_data.get('message', ''),
                    'server_time': datetime.now().isoformat()
                }
            else:
                return {
                    'type': 'response',
                    'message': f'已收到您的消息: {message}',
                    'server_time': datetime.now().isoformat()
                }
        except json.JSONDecodeError:
            # 非 JSON 格式，直接回显
            return {
                'type': 'echo',
                'message': f'回显: {message}',
                'server_time': datetime.now().isoformat()
            }
            
    def _send_message(self, client_socket: socket.socket, message: dict):
        """
        发送消息给客户端
        
        Args:
            client_socket: 客户端 socket
            message: 消息字典
        """
        try:
            message_json = json.dumps(message, ensure_ascii=False)
            client_socket.sendall(message_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            
    def _close_client(self, client_socket: socket.socket, client_address: tuple):
        """
        关闭客户端连接
        
        Args:
            client_socket: 客户端 socket
            client_address: 客户端地址
        """
        try:
            client_socket.close()
            with self.client_lock:
                self.clients = [c for c in self.clients if c['address'] != client_address]
            logger.info(f"已关闭客户端连接: {client_address}")
        except Exception as e:
            logger.error(f"关闭客户端连接时出错: {e}")
            
    def stop(self):
        """停止服务端"""
        logger.info("正在关闭服务端...")
        self.is_running = False
        
        # 关闭所有客户端连接
        with self.client_lock:
            for client in self.clients:
                try:
                    client['socket'].close()
                except:
                    pass
            self.clients.clear()
        
        # 关闭服务端 socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
        logger.info("服务端已关闭")
        
    def get_connected_clients(self) -> list:
        """获取已连接的客户端列表"""
        with self.client_lock:
            return [{
                'address': c['address'],
                'connected_at': c['connected_at'].isoformat()
            } for c in self.clients]


def main():
    """主函数"""
    # 创建服务端实例
    server = TCPServer(host='0.0.0.0', port=8888, max_connections=10)
    
    try:
        # 启动服务端
        server.start()
    except KeyboardInterrupt:
        logger.info("\n接收到中断信号，正在关闭服务端...")
        server.stop()


if __name__ == '__main__':
    main()
