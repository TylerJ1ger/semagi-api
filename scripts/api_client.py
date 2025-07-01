#!/usr/bin/env python3
"""
SEMagi API客户端脚本

该脚本提供了一个简单易用的Python客户端，用于与SEMagi API进行交互。
主要功能包括：
1. 创建关键词分组任务
2. 查询任务状态
3. 获取任务结果
4. 智能等待机制（基于预计时间）

使用方法:
    python api_client.py --api-key YOUR_API_KEY --function group-only --file keywords.json --task-name "my_task"
    python api_client.py --api-key YOUR_API_KEY --function scrap-and-group --file keywords.csv --task-name "my_task"

依赖库:
    pip install requests
"""

import argparse
import base64
import json
import os
import sys
import time
from typing import Dict, Any, Optional, List
import requests
from urllib.parse import urljoin
from pathlib import Path


class SEMagiAPIClient:
    """SEMagi API客户端类"""
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000", polling_config: Optional[Dict[str, Any]] = None):
        """
        初始化API客户端
        
        Args:
            api_key: API密钥
            base_url: API基础URL，默认为本地开发环境
            polling_config: 轮询配置
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'SEMagi-Python-Client/1.0'
        })
        
        # 轮询配置
        self.polling_config = polling_config or {
            "respect_estimate_time": True,
            "custom_interval_seconds": 5,
            "min_interval_seconds": 2,
            "max_interval_seconds": 30
        }
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        发送HTTP请求的通用方法
        
        Args:
            method: HTTP方法 (GET, POST, etc.)
            endpoint: API端点路径
            **kwargs: 传递给requests的其他参数
            
        Returns:
            requests.Response对象
            
        Raises:
            requests.exceptions.RequestException: 网络请求错误
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            raise
    
    def create_task(self, function: str, file_path: str, task_name: str, **params) -> Dict[str, Any]:
        """
        创建新的处理任务
        
        Args:
            function: 功能类型 ('group-only' 或 'scrap-and-group')
            file_path: 要处理的文件路径
            task_name: 任务名称
            **params: 其他可选参数
            
        Returns:
            包含任务信息的字典，包括task_id和estimate_time
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 参数错误
            requests.exceptions.RequestException: API请求错误
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取并编码文件内容
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 验证文件类型
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if function == 'group-only' and file_ext not in ['.json']:
            raise ValueError(f"group-only功能需要JSON文件，当前文件类型: {file_ext}")
        elif function == 'scrap-and-group' and file_ext not in ['.csv', '.txt']:
            raise ValueError(f"scrap-and-group功能需要CSV或TXT文件，当前文件类型: {file_ext}")
        
        # 准备请求数据
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        payload = {
            'function': function,
            'task_name': task_name,
            'file_name': file_name,
            'file_content': encoded_content,
            **params
        }
        
        print(f"🚀 创建任务: {task_name}")
        print(f"   功能: {function}")
        print(f"   文件: {file_name} ({len(file_content)} bytes)")
        
        # 发送请求
        response = self._make_request(
            'POST', 
            '/api/tasks',
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 201, 202, 409]:
            result = response.json()
            status = result.get('status', 'unknown')
            
            # 处理重复任务情况 (409状态码或status为duplicated)
            if response.status_code == 409 or status == 'duplicated':
                task_id = result.get('task_id')
                task_name = result.get('task_name', task_name)
                message = result.get('message', 'Task already exists')
                
                print(f"⚠️  {message}")
                # 返回重复任务信息，但标记为duplicated状态
                return {
                    'task_id': task_id,
                    'status': 'duplicated',
                    'task_name': task_name,
                    'message': message,
                    'estimate_time': 0  # 重复任务不需要等待
                }
            
            # 处理正常任务创建
            task_id = result.get('task_id')
            estimate_time = result.get('estimate_time', 0)
            message = result.get('message', 'Task created')
            
            print(f"✅ {message}")
            print(f"   任务ID: {task_id}")
            if estimate_time > 0:
                print(f"   预计完成时间: {estimate_time}秒")
            
            return result
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('detail', error_data.get('error', error_data.get('message', f'HTTP {response.status_code}')))
            print(f"❌ 任务创建失败: {error_message}")
            raise requests.exceptions.HTTPError(f"API Error: {error_message}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含任务状态信息的字典
            
        Raises:
            requests.exceptions.RequestException: API请求错误
        """
        response = self._make_request('GET', f'/api/tasks/{task_id}/status')
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError(f"任务不存在: {task_id}")
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('detail', error_data.get('error', f'HTTP {response.status_code}'))
            raise requests.exceptions.HTTPError(f"查询状态失败: {error_message}")
    
    def get_task_results(self, task_id: str) -> Dict[str, Any]:
        """
        获取完成任务的结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含任务结果的字典
            
        Raises:
            requests.exceptions.RequestException: API请求错误
        """
        response = self._make_request('GET', f'/api/tasks/{task_id}/results')
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError(f"任务结果不存在: {task_id}")
        elif response.status_code == 409:
            raise ValueError(f"任务尚未完成: {task_id}")
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_message = error_data.get('detail', error_data.get('error', f'HTTP {response.status_code}'))
            raise requests.exceptions.HTTPError(f"获取结果失败: {error_message}")
    
    def get_task_results_with_retry(self, task_id: str, estimate_time: int = 0, max_retries: int = 3) -> Dict[str, Any]:
        """
        带重试机制的结果获取
        
        Args:
            task_id: 任务ID
            estimate_time: 初始预计时间（秒）
            max_retries: 最大重试次数
            
        Returns:
            包含任务结果的字典
            
        Raises:
            requests.exceptions.RequestException: API请求错误
        """
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                results = self.get_task_results(task_id)
                return results
            except ValueError as e:
                if "任务尚未完成" in str(e):
                    retry_count += 1
                    
                    if retry_count > max_retries:
                        print(f"❌ 结果获取失败，请查看邮箱通知或前往网页端查询")
                        raise
                    
                    # 计算重试等待时间
                    if retry_count == 1:
                        wait_time = max(5, estimate_time // 2)
                    elif retry_count == 2:
                        wait_time = max(10, estimate_time)
                    else:
                        wait_time = max(15, int(estimate_time * 1.5))
                    
                    print(f"   ⏳ 结果准备中，{wait_time}秒后重试...")
                    
                    # 显示倒计时
                    for remaining in range(wait_time, 0, -1):
                        print(f"\r   等待重试... {remaining}秒", end="", flush=True)
                        time.sleep(1)
                    print(f"\r   重试获取结果中...        ")
                else:
                    # 其他错误直接抛出
                    raise
            except Exception as e:
                # 网络错误等其他异常也直接抛出
                raise
    
    def wait_for_completion(self, task_id: str, estimate_time: int = 0, max_wait: int = 1800) -> Dict[str, Any]:
        """
        等待任务完成，使用智能轮询策略
        
        Args:
            task_id: 任务ID
            estimate_time: 预计完成时间（秒）
            max_wait: 最大等待时间（秒），默认30分钟
            
        Returns:
            最终的任务状态信息
            
        Raises:
            TimeoutError: 超过最大等待时间
            requests.exceptions.RequestException: API请求错误
        """
        start_time = time.time()
        check_count = 0
        error_count = 0  # 独立的错误重试计数器
        
        print(f"⏳ 等待任务完成: {task_id}")
        
        # 获取轮询配置
        respect_estimate_time = self.polling_config.get("respect_estimate_time", True)
        custom_interval = self.polling_config.get("custom_interval_seconds", 5)
        min_interval = self.polling_config.get("min_interval_seconds", 2)
        max_interval = self.polling_config.get("max_interval_seconds", 30)
        limited_retry_strategy = self.polling_config.get("limited_retry_strategy", True)
        max_retries = self.polling_config.get("max_retries", 3)
        retry_on_error = self.polling_config.get("retry_on_error", True)
        
        if estimate_time > 0 and respect_estimate_time:
            print(f"   预计等待时间: {estimate_time}秒")
            print(f"   等待预计时间完成...")
            
            # 先等待预计时间（带进度显示）
            wait_start = time.time()
            while True:
                elapsed_wait = time.time() - wait_start
                if elapsed_wait >= estimate_time:
                    break
                
                remaining = estimate_time - elapsed_wait
                progress = (elapsed_wait / estimate_time) * 100
                print(f"\r   等待中... {progress:.1f}% (剩余: {remaining:.0f}s)", end="", flush=True)
                time.sleep(1)
            
            print(f"\n   预计时间已到，开始检查任务状态...")
        elif not respect_estimate_time:
            print(f"   🔧 使用自定义轮询间隔: {custom_interval}秒")
            if estimate_time > 0:
                print(f"   📊 预计等待时间: {estimate_time}秒 (已忽略)")
            polling_info = "无限轮询直到完成" if not limited_retry_strategy else f"最多轮询{max_retries}次"
            print(f"   🔄 轮询策略: {polling_info}")
            print(f"   ⚠️  错误重试: 固定3次")
            print(f"   ⚡ 立即开始轮询...")
        
        while True:
            elapsed = time.time() - start_time
            
            # 检查是否超过最大等待时间
            if elapsed > max_wait:
                raise TimeoutError(f"任务等待超时 ({max_wait}秒)")
            
            try:
                status_info = self.get_task_status(task_id)
                status = status_info.get('status', 'unknown')
                check_count += 1
                error_count = 0  # 成功获取状态，重置错误计数器
                
                print(f"   [{check_count:02d}] 状态: {status} (已等待 {elapsed:.1f}s)", end="")
                
                # 显示剩余时间估计
                if estimate_time > 0 and status == 'running':
                    remaining_estimate = max(0, estimate_time - elapsed)
                    if 'estimate_time' in status_info:
                        remaining_estimate = status_info['estimate_time']
                    print(f" - 预计剩余: {remaining_estimate:.0f}s")
                else:
                    print()
                
                # 检查任务是否完成
                if status == 'completed':
                    # 检查状态信息中是否包含结果数据
                    if 'result' in status_info and status_info['result']:
                        # 状态信息中包含结果数据，显示结果
                        print(f"✅ 任务完成! (总耗时: {elapsed:.1f}s)")
                        result_data = status_info['result']
                        result_data['status'] = 'completed'
                        # 标记已经显示过结果，避免重复显示
                        result_data['_already_displayed'] = True
                        self._display_results(result_data)
                        return result_data
                    
                    # 只在前几次验证时检查结果可用性，避免过度API调用
                    if check_count <= 3:
                        try:
                            self.get_task_results(task_id)
                            print(f"✅ 任务完成! (总耗时: {elapsed:.1f}s)")
                            final_status = dict(status_info)
                            final_status['status'] = 'completed'
                            return final_status
                        except ValueError as e:
                            if "任务尚未完成" in str(e):
                                status = 'running'  # 强制改为running状态继续等待
                            else:
                                print(f"✅ 任务完成! (总耗时: {elapsed:.1f}s)")
                                final_status = dict(status_info)
                                final_status['status'] = 'completed'
                                return final_status
                        except Exception:
                            print(f"✅ 任务完成! (总耗时: {elapsed:.1f}s)")
                            final_status = dict(status_info)
                            final_status['status'] = 'completed'
                            return final_status
                    else:
                        # 超过3次验证后，标记为已完成状态，让后续重试机制处理结果获取
                        print(f"✅ 任务完成! (总耗时: {elapsed:.1f}s)")
                        final_status = dict(status_info)
                        final_status['status'] = 'completed'
                        return final_status
                elif status in ['failed', 'error', 'cancelled']:
                    error_msg = status_info.get('message', f'任务状态: {status}')
                    print(f"❌ 任务失败: {error_msg}")
                    # 确保返回的状态信息包含正确的status字段
                    final_status = dict(status_info)
                    final_status['status'] = status
                    return final_status
                
                # 动态调整轮询间隔
                if not respect_estimate_time:
                    # 使用自定义固定间隔
                    interval = max(min_interval, min(custom_interval, max_interval))
                    print(f" - 下次检查: {interval}s")
                elif estimate_time > 0 and elapsed >= estimate_time:
                    # 预计时间已过，使用较短的间隔
                    overtime = elapsed - estimate_time
                    if overtime < 30:
                        interval = 5  # 前30秒每5秒查询一次
                    elif overtime < 120:
                        interval = 10  # 前2分钟每10秒查询一次
                    else:
                        interval = 15  # 超过2分钟每15秒查询一次
                elif estimate_time > 0:
                    # 预计时间内，不应该到达这里（因为上面已经等待了预计时间）
                    interval = max(5, estimate_time * 0.1)
                else:
                    # 没有预计时间：立即开始轮询
                    if check_count <= 3:
                        interval = 5
                    elif check_count <= 10:
                        interval = 10
                    else:
                        interval = 15
                
                time.sleep(interval)
                
                # 检查是否超过轮询限制（仅在有限轮询模式下）
                if limited_retry_strategy and check_count >= max_retries:
                    print(f"\n⚠️  已达到最大轮询次数 ({max_retries})，任务可能仍在处理中")
                    print(f"   📋 任务ID: {task_id}")
                    print(f"   💡 建议稍后手动查询任务状态")
                    final_status = dict(status_info)
                    final_status['status'] = 'polling_limit_reached'
                    return final_status
                
            except KeyboardInterrupt:
                print(f"\n⚠️  用户中断，任务仍在后台运行: {task_id}")
                return {'status': 'interrupted', 'task_id': task_id}
            except Exception as e:
                if not retry_on_error:
                    print(f"\n❌ 状态查询失败: {e}")
                    raise
                
                error_count += 1
                error_message = f"状态查询失败 (第{error_count}次): {e}"
                
                # 错误重试固定为3次
                if error_count <= 3:
                    print(f"\n⚠️  {error_message}")
                    print(f"   🔄 网络错误重试... (剩余{3 - error_count + 1}次)")
                    time.sleep(5)
                    continue
                else:
                    print(f"\n❌ {error_message}")
                    print(f"   🚫 达到最大错误重试次数 (3)，停止重试")
                    raise
    
    def process_file(self, function: str, file_path: str, task_name: str, 
                     wait_for_completion: bool = True, **params) -> Dict[str, Any]:
        """
        完整的文件处理流程：创建任务 -> 等待完成 -> 获取结果
        
        Args:
            function: 功能类型
            file_path: 文件路径
            task_name: 任务名称
            wait_for_completion: 是否等待任务完成
            **params: 其他参数
            
        Returns:
            包含完整处理结果的字典
        """
        # 创建任务
        task_info = self.create_task(function, file_path, task_name, **params)
        task_id = task_info['task_id']
        task_status = task_info.get('status', 'processing')
        estimate_time = task_info.get('estimate_time', 0)
        
        # 处理重复任务 - 直接尝试获取结果
        if task_status == 'duplicated':
            print(f"🔍 检查现有任务结果...")
            try:
                results = self.get_task_results(task_id)
                if results and isinstance(results, dict) and results:
                    print(f"✅ 找到现有任务结果!")
                    self._display_results(results)
                    results['status'] = 'completed'
                    return results
            except Exception as e:
                print(f"⚠️  无法获取现有任务结果: {e}")
                print(f"   将尝试查询任务状态...")
                # 继续执行等待逻辑
        
        if not wait_for_completion:
            print(f"📋 任务已创建，ID: {task_id}")
            return task_info
        
        # 等待完成
        try:
            final_status = self.wait_for_completion(task_id, estimate_time)
            
            if final_status.get('status') == 'completed':
                # 检查是否已经显示过结果
                if final_status.get('_already_displayed'):
                    # 结果已经在wait_for_completion中显示过了，直接返回
                    return final_status
                
                # 使用重试机制获取结果
                try:
                    results = self.get_task_results_with_retry(task_id, estimate_time)
                    if results and isinstance(results, dict) and results:
                        self._display_results(results)
                        # 确保返回的结果包含正确的状态
                        results['status'] = 'completed'
                        return results
                    else:
                        print("⚠️  获取到空结果")
                        final_status['status'] = 'completed'
                        return final_status
                except Exception as e:
                    print(f"⚠️  获取结果失败: {e}")
                    final_status['status'] = 'completed'
                    return final_status
            else:
                return final_status
                
        except KeyboardInterrupt:
            print(f"\n⚠️  进程被中断，但任务仍在后台运行")
            print(f"   可以稍后使用以下命令查询状态:")
            print(f"   python {sys.argv[0]} --check-status {task_id}")
            return {'status': 'interrupted', 'task_id': task_id}
    
    def _display_results(self, results: Dict[str, Any]) -> None:
        """
        格式化显示任务结果 - 支持多种响应格式
        
        Args:
            results: 任务结果字典
        """
        print("\n" + "="*60)
        print("📊 任务结果")
        print("="*60)
        
        # 检测响应格式版本
        response_version = results.get('response_version', '1.0')
        
        if response_version == '2.0' or 'task' in results:
            # 新格式 (v2.0) - 嵌套结构
            self._display_v2_results(results)
        elif isinstance(results, list) and len(results) > 0:
            # 旧格式 - 数组结构
            self._display_legacy_results(results[0])
        else:
            # 未知格式 - 尝试显示所有可用信息
            self._display_unknown_format(results)
        
        print("="*60)
    
    def _display_v2_results(self, results: Dict[str, Any]) -> None:
        """显示v2.0格式的结果"""
        task_data = results.get('task', {})
        files_data = results.get('files', {})
        parameters_data = results.get('parameters', {})
        quality_data = results.get('quality', {})
        
        
        # 基本信息
        if isinstance(task_data, dict):
            task_name = task_data.get('name') or task_data.get('task_name')
            if task_name:
                print(f"任务名称: {task_name}")
            
            function = task_data.get('function')
            if function:
                print(f"处理功能: {function}")
            
            created_time = task_data.get('created_time')
            if created_time:
                from datetime import datetime
                if isinstance(created_time, (int, float)):
                    dt = datetime.fromtimestamp(created_time / 1000)
                    print(f"创建时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 文件信息和下载链接
        if isinstance(files_data, dict):
            print(f"\n📁 文件下载:")
            found_links = False
            for file_type, file_info in files_data.items():
                if isinstance(file_info, dict):
                    filename = file_info.get('filename', f'{file_type} 文件')
                    download_link = file_info.get('download_link')
                    
                    if download_link:
                        print(f"  {file_type.upper()}: {download_link}")
                        print(f"    文件名: {filename}")
                        found_links = True
            
            if not found_links:
                print(f"  下载链接生成中...")
        
        # 参数信息
        if isinstance(parameters_data, dict):
            print(f"\n⚙️  处理参数:")
            for param_group, params in parameters_data.items():
                if isinstance(params, dict):
                    print(f"  {param_group}:")
                    for key, value in params.items():
                        if isinstance(value, bool):
                            print(f"    {key}: {'启用' if value else '禁用'}")
                        else:
                            print(f"    {key}: {value}")
        
        # 质量评分
        if isinstance(quality_data, dict) and quality_data:
            print(f"\n📈 质量评分:")
            for key, value in quality_data.items():
                if isinstance(value, (int, float)):
                    print(f"  {key}: {value:.1f}")
                else:
                    print(f"  {key}: {value}")
    
    def _display_legacy_results(self, result: Dict[str, Any]) -> None:
        """显示旧格式的结果"""
        # 基本信息
        task_name = result.get('task name')
        if task_name:
            print(f"任务名称: {task_name}")
        
        function = result.get('function')
        if function:
            print(f"处理功能: {function}")
        
        created_time = result.get('created time')
        if created_time:
            print(f"创建时间: {created_time}")
        
        # 信用点信息
        credit_cost = result.get('credit cost')
        credit_new = result.get('credit new')
        if credit_cost:
            print(f"消耗积分: {credit_cost}")
        if credit_new:
            print(f"剩余积分: {credit_new}")
        
        # 算法信息
        algorithm = result.get('algorithm')
        min_similarity = result.get('min_similarity')
        if algorithm:
            print(f"分组算法: {algorithm}")
        if min_similarity:
            print(f"最小相似度: {min_similarity}")
        
        # 下载链接
        csv_link = result.get('csv download link')
        json_link = result.get('json download link')
        csv_filename = result.get('csv file name')
        
        if csv_link or json_link:
            print(f"\n📁 文件下载:")
            if csv_link:
                print(f"  CSV: {csv_link}")
                if csv_filename:
                    print(f"    文件名: {csv_filename}")
            if json_link:
                print(f"  JSON: {json_link}")
        
        # 质量评分
        quality_fields = ['grouping_quality_score', 'grouping_coverage_score', 
                         'grouping_balance_score', 'grouping_similarity_score']
        quality_scores = {field: result.get(field) for field in quality_fields if result.get(field)}
        
        if quality_scores:
            print(f"\n📈 质量评分:")
            for field, score in quality_scores.items():
                field_name = field.replace('grouping_', '').replace('_', ' ').title()
                print(f"  {field_name}: {score:.1f}")
    
    def _display_unknown_format(self, results: Dict[str, Any]) -> None:
        """显示未知格式的结果"""
        print("⚠️  未知的结果格式，显示所有可用信息:")
        
        if isinstance(results, dict):
            for key, value in results.items():
                if key not in ['status', 'response_version']:
                    if isinstance(value, (dict, list)):
                        print(f"  {key}: {type(value).__name__} (包含 {len(value)} 项)")
                    else:
                        print(f"  {key}: {value}")
        else:
            print(f"  数据类型: {type(results).__name__}")
            print(f"  内容: {results}")


def load_settings():
    """加载配置文件"""
    # 查找配置文件的路径
    script_dir = Path(__file__).parent.parent  # 回到client目录
    settings_path = script_dir / "settings.json"
    
    default_settings = {
        "api_key": "",
        "base_url": "http://localhost:8000",
        "task": {
            "function": "group-only",
            "file": "keywords.json",
            "task_name": "my_task"
        },
        "defaults": {
            "grouper": "hierarchical_clustering",
            "min_similarity": 0.5,
            "range": 10,
            "country": "us",
            "language": "en",
            "numbers": 10,
            "force_group": True,
            "force_group_min_similarity": 0.2
        },
        "timeout": {
            "request_timeout": 30,
            "max_wait_time": 1800
        },
        "display": {
            "show_debug": False,
            "show_progress": True
        },
        "polling": {
            "respect_estimate_time": True,
            "custom_interval_seconds": 5,
            "min_interval_seconds": 2,
            "max_interval_seconds": 30,
            "limited_retry_strategy": True,
            "max_retries": 3,
            "retry_on_error": True
        }
    }
    
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # 合并默认设置
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in settings[key]:
                                settings[key][sub_key] = sub_value
                return settings
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️  配置文件读取失败: {e}")
            print(f"   使用默认配置")
    
    return default_settings


def main():
    """主函数：处理命令行参数并执行相应操作"""
    # 加载配置文件
    settings = load_settings()
    
    parser = argparse.ArgumentParser(
        description='SEMagi API客户端 - 关键词分组和搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 创建分组任务
  python api_client.py --function group-only --file keywords.json --task-name "my_grouping_task"
  
  # 创建搜索+分组任务
  python api_client.py --function scrap-and-group --file keywords.csv --task-name "my_scraping_task"
  
  # 查询任务状态
  python api_client.py --check-status TASK_ID
  
  # 获取任务结果
  python api_client.py --get-results TASK_ID
  
支持的文件格式:
  - group-only: .json
  - scrap-and-group: .csv, .txt
        """
    )
    
    # 基本参数
    parser.add_argument('--base-url', help=f'API基础URL (默认: {settings["base_url"]})')
    
    # 操作参数 - 使用配置文件的默认值
    task_config = settings.get('task', {})
    parser.add_argument('--function', choices=['group-only', 'scrap-and-group'], 
                       default=task_config.get('function'), help=f'处理功能 (默认: {task_config.get("function", "未配置")})')
    parser.add_argument('--file', default=task_config.get('file'),
                       help=f'要处理的文件路径 (默认: {task_config.get("file", "未配置")})')
    parser.add_argument('--task-name', default=task_config.get('task_name'),
                       help=f'任务名称 (默认: {task_config.get("task_name", "未配置")})')
    parser.add_argument('--no-wait', action='store_true', help='不等待任务完成')
    
    # 查询操作
    parser.add_argument('--check-status', metavar='TASK_ID', help='查询指定任务的状态')
    parser.add_argument('--get-results', metavar='TASK_ID', help='获取指定任务的结果')
    
    # 可选参数 - 使用配置文件的默认值
    defaults = settings['defaults']
    parser.add_argument('--grouper', choices=['hierarchical_clustering', 'jaccard'], 
                       default=defaults['grouper'], help=f'分组算法 (默认: {defaults["grouper"]})')
    parser.add_argument('--min-similarity', type=float, default=defaults['min_similarity'], 
                       help=f'最小相似度 (默认: {defaults["min_similarity"]})')
    parser.add_argument('--range', type=int, default=defaults['range'], 
                       help=f'搜索范围 (默认: {defaults["range"]})')
    parser.add_argument('--country', default=defaults['country'], 
                       help=f'搜索国家代码 (默认: {defaults["country"]})')
    parser.add_argument('--language', default=defaults['language'], 
                       help=f'搜索语言代码 (默认: {defaults["language"]})')
    parser.add_argument('--numbers', type=int, default=defaults['numbers'], 
                       help=f'搜索结果数量 (默认: {defaults["numbers"]})')
    
    args = parser.parse_args()
    
    # 从配置文件获取API密钥
    api_key = settings.get('api_key')
    if not api_key:
        print("❌ 错误: 需要在settings.json中配置API密钥")
        print("   请复制 settings.example.json 为 settings.json 并填入你的API密钥")
        sys.exit(1)
    
    # 确定基础URL
    base_url = args.base_url or settings['base_url']
    
    # 创建客户端，传递轮询配置
    polling_config = settings.get('polling', {})
    client = SEMagiAPIClient(api_key, base_url, polling_config)
    
    try:
        # 查询状态操作
        if args.check_status:
            print(f"🔍 查询任务状态: {args.check_status}")
            status = client.get_task_status(args.check_status)
            print(f"状态: {status.get('status', 'unknown')}")
            if 'message' in status:
                print(f"信息: {status['message']}")
            if 'estimate_time' in status:
                print(f"预计剩余时间: {status['estimate_time']}秒")
            return
        
        # 获取结果操作
        if args.get_results:
            print(f"📋 获取任务结果: {args.get_results}")
            results = client.get_task_results(args.get_results)
            client._display_results(results)
            return
        
        # 创建任务操作
        if not args.function:
            parser.error("需要指定 --function 参数或在settings.json中配置task.function")
        if not args.file:
            parser.error("需要指定 --file 参数或在settings.json中配置task.file")
        if not args.task_name:
            parser.error("需要指定 --task-name 参数或在settings.json中配置task.task_name")
        
        # 准备参数
        params = {
            'grouper': args.grouper,
            'min_similarity': args.min_similarity,
            'range_': args.range,
            'country': args.country,
            'language': args.language,
            'numbers': args.numbers,
        }
        
        # 执行完整流程
        result = client.process_file(
            function=args.function,
            file_path=args.file,
            task_name=args.task_name,
            wait_for_completion=not args.no_wait,
            **params
        )
        
        # 输出最终状态
        final_status = result.get('status', 'unknown')
        if final_status == 'completed':
            print(f"\n🎉 任务完成成功!")
        elif final_status == 'interrupted':
            print(f"\n⚠️  任务被中断，但仍在后台运行")
            print(f"任务ID: {result.get('task_id', 'N/A')}")
        else:
            print(f"\n❌ 任务状态: {final_status}")
        
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ 参数错误: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()