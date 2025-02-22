from web3 import Web3
from eth_account import Account
import json
import time
import random
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz  # 引入pytz库

# 定义时区
wib = pytz.timezone('Asia/Shanghai')

# 加载环境变量
load_dotenv()

# 网络配置
RPC_URL = "https://rpc-testnet.inichain.com"
CHAIN_ID = 7234

# 合约地址
DAILY_CHECKIN_CONTRACT = "0x73439c32e125B28139823fE9C6C079165E94C6D1"
ROUTER_CONTRACT = "0x4ccB784744969D9B63C15cF07E622DDA65A88Ee7"
WINI_CONTRACT = "0xfbECae21C91446f9c7b87E4e5869926998f99ffe"
USDT_CONTRACT = "0xcF259Bca0315C6D32e877793B6a10e97e7647FdE"

# 代币小数位
USDT_DECIMALS = 18
INI_DECIMALS = 18

# 必需的最小ABI
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

DAILY_CHECKIN_ABI = [
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "userCheckInStatus",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# WINI（Wrapped INI）的ABI
WINI_ABI = [
    {
        "constant": False,
        "inputs": [],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "wad", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# 创建代币的ABI
TOKEN_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "string", "name": "symbol", "type": "string"},
            {"internalType": "uint256", "name": "initialSupply", "type": "uint256"},
            {"internalType": "uint8", "name": "decimals", "type": "uint8"}
        ],
        "name": "createToken",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "symbol", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "totalSupply", "type": "uint256"},
            {"indexed": False, "internalType": "uint8", "name": "decimals", "type": "uint8"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "TokenCreated",
        "type": "event"
    }
]


TOKEN_FACTORY_CONTRACT = "0x01AA0e004F7e7591f2fc2712384dF9B5FDB759DD"


w3 = Web3(Web3.HTTPProvider(RPC_URL))

class IniChainBot:
    def __init__(self, private_key):
        self.account = Account.from_key(private_key)
        self.address = self.account.address
        self.router_contract = w3.eth.contract(address=ROUTER_CONTRACT, abi=ROUTER_ABI)
        self.checkin_contract = w3.eth.contract(address=DAILY_CHECKIN_CONTRACT, abi=DAILY_CHECKIN_ABI)
        self.wini_contract = w3.eth.contract(address=WINI_CONTRACT, abi=WINI_ABI)
        self.last_checkin = {}
        
    def get_dynamic_gas_price(self, priority="normal"):
        """根据当前网络状况获取动态Gas价格"""
        base_gas_price = w3.eth.gas_price
        
        multipliers = {
            "low": 1.1,
            "normal": 1.2,
            "high": 1.5
        }
        
        gas_price = int(base_gas_price * multipliers[priority])
        
    
        max_gas_price = 5 * 10**9
        return min(gas_price, max_gas_price)

    def get_gas_price(self):
        """获取正常交易的最优Gas价格"""
        return self.get_dynamic_gas_price("normal")
        
    def get_approve_gas_price(self):
        """获取Approve操作的Gas价格，优先级更高"""
        return self.get_dynamic_gas_price("high")

    def format_amount(self, amount, decimals):
        """格式化金额，显示为正确的小数位"""
        return amount / (10 ** decimals)

    def check_daily_checkin_status(self):
        """检查每日签到是否可用"""
        try:
            has_checked_in = self.checkin_contract.functions.userCheckInStatus(self.address).call()
            if not has_checked_in:
                return True
                
            print(f"[{self.address}] 签到仍在冷却中")
            return False
            
        except Exception as e:
            print(f"[{self.address}] 检查签到状态时出错: {str(e)}")
            return False

    def daily_checkin(self, account_info):
        """执行每日签到"""
        try:
            nonce = w3.eth.get_transaction_count(self.address)
            gas_price = self.get_gas_price()
            
            print(f"[{account_info}] 开始每日签到...")
            print(f"[{account_info}] Gas价格: {gas_price / 1e9:.2f} Gwei")
            
            # 估算Gas限制
            try:
                gas_estimate = w3.eth.estimate_gas({
                    'from': self.address,
                    'to': DAILY_CHECKIN_CONTRACT,
                    'value': 0,
                    'data': '0x183ff085', 
                    'gasPrice': gas_price,
                    'nonce': nonce
                })
                print(f"[{account_info}] 估算Gas: {gas_estimate}")
            except Exception as e:
                error_message = str(e)
                if "Today's check-in has been completed" in error_message:
                    print(f"[{account_info}] 今日签到已完成")
                    return False
                else:
                    print(f"[{account_info}] 估算Gas时出错: {error_message}")
                    gas_estimate = 150000  
                
            transaction = {
                'from': self.address,
                'to': DAILY_CHECKIN_CONTRACT,
                'value': 0,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID,
                'data': '0x183ff085'  
            }

            signed_txn = w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            
            receipt = self.wait_for_transaction(tx_hash)
            
            if receipt and receipt['status'] == 1:
                self.last_checkin[self.address] = datetime.now(wib)
                print(f"[{account_info}] 签到成功: {tx_hash.hex()}")
                return True
            else:
                if receipt:
                    print(f"[{account_info}] 签到失败! Gas消耗: {receipt.get('gasUsed', '未知')}")
                    try:
                      
                        tx = w3.eth.get_transaction(tx_hash)
                        print(f"[{account_info}] 交易详情:")
                        print(f"  Gas价格: {tx.get('gasPrice', '未知')}")
                        print(f"  Gas限制: {tx.get('gas', '未知')}")
                        print(f"  Nonce: {tx.get('nonce', '未知')}")
                        print(f"  值: {tx.get('value', '未知')}")
                    except Exception as e:
                        print(f"[{account_info}] 获取交易详情时出错: {str(e)}")
                return False
                
        except Exception as e:
            print(f"[{account_info}] 签到时出错: {str(e)}")
            return False

    def get_token_balance(self, token_address):
        """获取代币余额"""
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(self.address).call()
        return balance

    def wait_for_transaction(self, tx_hash, timeout=300):
        """等待交易被挖矿并返回回执"""
        start_time = time.time()
        print(f"[{self.address}] 等待交易确认: {tx_hash.hex()}")
        
        while True:
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                if receipt is not None:
                    return receipt
            except Exception as e:
                pass
            
            if time.time() - start_time > timeout:
                print(f"[{self.address}] 等待确认时出错: 交易 {tx_hash.hex()} 在 {timeout} 秒后未被确认")
                return None
            
            print(f"[{self.address}] 仍在等待确认... ({int(time.time() - start_time)} 秒)")
            time.sleep(10)

    def approve_token(self, token_address, amount, account_info):
        """为路由器批准代币"""
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        try:
            print(f"[{account_info}] 开始批准流程...")
            
            # 先检查允许额度
            current_allowance = token_contract.functions.allowance(self.address, ROUTER_CONTRACT).call()
            if current_allowance >= amount:
                print(f"[{account_info}] 允许额度已足够，无需再次批准")
                return True
            
            nonce = w3.eth.get_transaction_count(self.address)
            gas_price = self.get_approve_gas_price()  # 使用更高的Gas价格进行批准
            
            print(f"[{account_info}] 发送批准交易，Gas价格: {gas_price / 1e9:.2f} Gwei")
            
         
            amount = int(amount)
            
            approve_txn = token_contract.functions.approve(
                ROUTER_CONTRACT,
                amount
            ).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })
            
            signed_txn = w3.eth.account.sign_transaction(approve_txn, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.wait_for_transaction(tx_hash)
            return receipt is not None and receipt['status'] == 1
            
        except Exception as e:
            print(f"[{account_info}] 批准时出错: {str(e)}")
            return False

    def get_token_price(self, token_in, token_out, amount_in):
        """从路由器获取代币价格"""
        try:
            path = [token_in, token_out]
            amount_in_wei = int(amount_in * 1e18)
            
        
            amounts_out = self.router_contract.functions.getAmountsOut(
                amount_in_wei,
                path
            ).call()
            
            return amounts_out[1] / 1e18
        except Exception as e:
            print(f"[{self.address}] 获取价格时出错: {str(e)}")
            return 0

    def swap_usdt_to_ini(self, amount, account_info):
        """将USDT兑换为INI"""
        try:
        
            amount_in_wei = int(amount * (10 ** USDT_DECIMALS))
            
            if not self.approve_token(USDT_CONTRACT, amount_in_wei, account_info):
                print(f"[{account_info}] 批准USDT失败")
                return
                
            nonce = w3.eth.get_transaction_count(self.address)
            gas_price = self.get_gas_price()
            deadline = int(time.time()) + 300  # 5分钟截止时间
            
     
            expected_out = self.get_token_price(USDT_CONTRACT, WINI_CONTRACT, amount)
            if expected_out == 0:
                print(f"[{account_info}] 获取价格失败，取消兑换")
                return
            
            min_out = int(expected_out * 1e18 * 0.95)  
            
            print(f"[{account_info}] 开始将USDT兑换为INI...")
            print(f"[{account_info}] Gas价格: {gas_price / 1e9:.2f} Gwei")
            print(f"[{account_info}] 金额: {amount:.6f} USDT")
            print(f"[{account_info}] 预期输出: {expected_out:.6f} INI")
            print(f"[{account_info}] 最小输出: {min_out / 1e18:.6f} INI")
            
          
            path = [USDT_CONTRACT, WINI_CONTRACT]
            
           
            try:
                gas_estimate = self.router_contract.functions.swapExactTokensForTokens(
                    amount_in_wei,
                    min_out,
                    path,
                    self.address,
                    deadline
                ).estimate_gas({
                    'from': self.address,
                    'gasPrice': gas_price,
                    'nonce': nonce
                })
                print(f"[{account_info}] 估算Gas: {gas_estimate}")
            except Exception as e:
                print(f"[{account_info}] 估算Gas时出错: {str(e)}")
                gas_estimate = 201306  # 成功交易的Gas限制
            
            swap_txn = self.router_contract.functions.swapExactTokensForTokens(
                amount_in_wei,  # USDT 数量
                min_out,        # 最小获得的 INI 数量
                path,           # 交易路径
                self.address,   # 接收地址
                deadline        # 截止时间
            ).build_transaction({
                'from': self.address,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })
            
            signed_txn = w3.eth.account.sign_transaction(swap_txn, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.wait_for_transaction(tx_hash)
            if receipt and receipt['status'] == 1:
                print(f"[{account_info}] USDT兑换INI成功!")
                return True
            else:
                print(f"[{account_info}] USDT兑换INI失败!")
                return False
                
        except Exception as e:
            print(f"[{account_info}] 兑换USDT为INI时出错: {str(e)}")
            return False

    def swap_ini_to_usdt(self, amount, account_info):
        """通过swapExactETHForTokens将INI兑换为USDT"""
        try:
            nonce = w3.eth.get_transaction_count(self.address)
            gas_price = self.get_gas_price()
            deadline = int(time.time()) + 300  # 5分钟截止时间
            
            # 将金额转换为wei
            amount_in_wei = w3.to_wei(amount, 'ether')
            
            # 获取预期输出金额
            expected_out = self.get_token_price(WINI_CONTRACT, USDT_CONTRACT, amount)
            if expected_out == 0:
                print(f"[{account_info}] 获取价格失败，取消兑换")
                return
            
            min_out = int(expected_out * 1e18 * 0.95)  # 5% 滑点
            
            print(f"[{account_info}] 开始将INI兑换为USDT...")
            print(f"[{account_info}] Gas价格: {gas_price / 1e9:.2f} Gwei")
            print(f"[{account_info}] 金额: {amount:.6f} INI")
            print(f"[{account_info}] 预期输出: {expected_out:.6f} USDT")
            print(f"[{account_info}] 最小输出: {min_out / 1e18:.6f} USDT")
            
            # 路径: WINI -> USDT
            path = [WINI_CONTRACT, USDT_CONTRACT]
            
            # 估算Gas限制
            try:
                gas_estimate = self.router_contract.functions.swapExactETHForTokens(
                    min_out,  # 最小输出金额
                    path,     # 路径
                    self.address,  # 接收地址
                    deadline  # 截止时间
                ).estimate_gas({
                    'from': self.address,
                    'value': amount_in_wei,
                    'gasPrice': gas_price,
                    'nonce': nonce
                })
                print(f"[{account_info}] 估算Gas: {gas_estimate}")
            except Exception as e:
                print(f"[{account_info}] 估算Gas时出错: {str(e)}")
                gas_estimate = 201306  # 成功交易的Gas限制
            
            # 构建交易
            swap_txn = self.router_contract.functions.swapExactETHForTokens(
                min_out,  # 最小输出金额
                path,     # 路径
                self.address,  # 接收地址
                deadline  # 截止时间
            ).build_transaction({
                'from': self.address,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'value': amount_in_wei,  # 兑换的INI金额
                'nonce': nonce,
                'chainId': CHAIN_ID
            })
            
            signed_txn = w3.eth.account.sign_transaction(swap_txn, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.wait_for_transaction(tx_hash)
            if receipt and receipt['status'] == 1:
                print(f"[{account_info}] INI兑换USDT成功!")
                return True
            else:
                print(f"[{account_info}] INI兑换USDT失败!")
                return False
                
        except Exception as e:
            print(f"[{account_info}] 兑换INI为USDT时出错: {str(e)}")
            return False

    def wrap_ini(self, amount):
        """将INI包装为WINI"""
        try:
            nonce = w3.eth.get_transaction_count(self.address)
            gas_price = self.get_gas_price()
            
            # 将金额转换为wei
            amount_in_wei = w3.to_wei(amount, 'ether')
            
            print(f"[{self.address}] 将 {amount:.6f} INI 包装为 WINI...")
            print(f"[{self.address}] Gas价格: {gas_price / 1e9:.2f} Gwei")
            
            # 估算Gas
            try:
                gas_estimate = self.wini_contract.functions.deposit().estimate_gas({
                    'from': self.address,
                    'value': amount_in_wei,
                    'gasPrice': gas_price,
                    'nonce': nonce
                })
                print(f"[{self.address}] 估算Gas: {gas_estimate}")
            except Exception as e:
                print(f"[{self.address}] 估算Gas时出错: {str(e)}")
                gas_estimate = 50000  # 回退Gas限制用于存款
            
            # 构建交易
            deposit_txn = self.wini_contract.functions.deposit().build_transaction({
                'from': self.address,
                'gas': gas_estimate,
                'gasPrice': gas_price,
                'value': amount_in_wei,
                'nonce': nonce,
                'chainId': CHAIN_ID
            })
            
            signed_txn = w3.eth.account.sign_transaction(deposit_txn, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            receipt = self.wait_for_transaction(tx_hash)
            if receipt and receipt['status'] == 1:
                print(f"[{self.address}] INI包装为WINI成功!")
                return True
            else:
                print(f"[{self.address}] INI包装为WINI失败!")
                return False
                
        except Exception as e:
            print(f"[{self.address}] 包装INI时出错: {str(e)}")
            return False

    def perform_swap(self, account_info):
        try:
            # 获取 INI 余额
            ini_balance = w3.eth.get_balance(self.address)
            formatted_ini_balance = w3.from_wei(ini_balance, 'ether')
            
            print(f"[{account_info}] 当前 INI 余额: {formatted_ini_balance:.6f}")
            
            # 如果 INI 余额小于 0.2，尝试用 USDT 兑换
            if formatted_ini_balance < 0.2:
                # 检查 USDT 余额
                usdt_balance = self.get_token_balance(USDT_CONTRACT)
                formatted_usdt_balance = self.format_amount(usdt_balance, USDT_DECIMALS)
                
                print(f"[{account_info}] INI 余额低于 0.2，当前 USDT 余额: {formatted_usdt_balance:.6f}")
                
                if usdt_balance > 0:
                    # 将 80-90% 的 USDT 换成 INI
                    swap_percentage = random.uniform(0.80, 0.90)
                    amount_to_swap = formatted_usdt_balance * swap_percentage
                    
                    print(f"[{account_info}] 将兑换 {amount_to_swap:.6f} USDT 到 INI ({swap_percentage*100:.1f}%)")
                    
                    self.swap_usdt_to_ini(amount_to_swap, account_info)
                else:
                    print(f"[{account_info}] USDT 余额为 0，无法兑换")
            else:
                # INI 余额充足，可以考虑兑换一部分为 USDT
                gas_price = self.get_gas_price()
                estimated_gas = 201306
                gas_cost = gas_price * estimated_gas
                safe_balance = ini_balance - (gas_cost * 1.2)
                
                if safe_balance > gas_cost:
                    swap_percentage = random.uniform(0.10, 0.25)
                    amount_to_swap = float(w3.from_wei(int(safe_balance * swap_percentage), 'ether'))
                    print(f"[{account_info}] INI 余额充足，将兑换 {amount_to_swap:.6f} INI 到 USDT ({swap_percentage*100:.1f}%)")
                    self.swap_ini_to_usdt(amount_to_swap, account_info)
                
        except Exception as e:
            print(f"[{account_info}] 兑换时出错: {str(e)}")

    def create_token(self, name, symbol, total_supply, decimals, account_info):
        """使用指定参数创建新代币"""
        try:
            token_factory = w3.eth.contract(address=TOKEN_FACTORY_CONTRACT, abi=TOKEN_FACTORY_ABI)
            
            # 将总供应量转换为wei格式
            total_supply_wei = int(total_supply * (10 ** decimals))
            
            nonce = w3.eth.get_transaction_count(self.address)
            gas_price = self.get_dynamic_gas_price("normal")  # 使用动态Gas价格
            
            print(f"[{account_info}] 开始创建代币...")
            print(f"[{account_info}] Gas价格: {gas_price / 1e9:.2f} Gwei")
            print(f"[{account_info}] 代币名称: {name}")
            print(f"[{account_info}] 代币符号: {symbol}")
            print(f"[{account_info}] 总供应量: {total_supply_wei}")
            print(f"[{account_info}] 小数位: {decimals}")
            
            # 使用与成功交易相同的Gas限制构建交易
            gas_limit = 1548128  # 成功交易的Gas限制
            estimated_gas_cost = gas_limit * gas_price / 1e18
            print(f"[{account_info}] 估算Gas费用: {estimated_gas_cost:.6f} INI")
            
            # 检查INI余额
            balance = w3.eth.get_balance(self.address)
            formatted_balance = w3.from_wei(balance, 'ether')
            print(f"[{account_info}] 当前余额: {formatted_balance:.6f} INI")
            
            if balance < (gas_limit * gas_price):
                print(f"[{account_info}] INI余额不足以支付Gas费用!")
                return False
            
            # 使用与成功交易完全相同的输入数据
            input_data = "0x8ab84b4a000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000186a000000000000000000000000000000000000000000000000000000000000000120000000000000000000000000000000000000000000000000000000000000004757364740000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000047573647400000000000000000000000000000000000000000000000000000000"
            
            # 构建交易
            transaction = {
                'from': self.address,
                'to': TOKEN_FACTORY_CONTRACT,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': CHAIN_ID,
                'data': input_data
            }
            
            # 签名并发送交易
            signed_txn = w3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"[{account_info}] 等待代币创建确认...")
            receipt = self.wait_for_transaction(tx_hash)
            
            if receipt and receipt['status'] == 1:
                print(f"[{account_info}] 代币创建成功!")
                print(f"[{account_info}] 交易哈希: {tx_hash.hex()}")
                return True
            else:
                print(f"[{account_info}] 代币创建失败!")
                if receipt:
                    print(f"[{account_info}] Gas消耗: {receipt.get('gasUsed', '未知')}")
                return False
            
        except Exception as e:
            print(f"[{account_info}] 创建代币时出错: {str(e)}")
            return False

def get_transaction_type(tx, bot_address, bot):
    """获取交易类型及详情"""
    if tx['to'] is None:
        return "合约创建", None
        
    # 检查每日签到
    if tx['to'].lower() == DAILY_CHECKIN_CONTRACT.lower():
        return "每日签到", None
        
    # 检查代币转移
    if tx['to'].lower() == ROUTER_CONTRACT.lower():
        if tx['value'] > 0:
            return "INI兑换USDT", f"{bot.format_amount(tx['value'], INI_DECIMALS):.6f} INI"
        else:
            return "USDT兑换INI", None
            
    # 默认交易
    if tx['from'].lower() == bot_address.lower():
        return "转出交易", f"{bot.format_amount(tx['value'], INI_DECIMALS):.6f} INI"
    else:
        return "转入交易", f"{bot.format_amount(tx['value'], INI_DECIMALS):.6f} INI"

def show_status(private_key, account_num):
    """显示账户状态"""
    # 初始化机器人
    bot = IniChainBot(private_key)
    account_info = f"账户 {account_num} | {bot.address[-4:]}"
    
    # 获取余额
    ini_balance = w3.eth.get_balance(bot.address) / 10**18
    usdt_balance = bot.get_token_balance(USDT_CONTRACT) / 10**18
    
    # 获取Gas价格
    gas_price = w3.eth.gas_price / 10**9
    
    # 估算费用
    checkin_gas = 150000  # 签到的估算Gas
    swap_gas = 300000     # 兑换的估算Gas
    
    checkin_fee = (checkin_gas * gas_price) / 10**9
    swap_fee = (swap_gas * gas_price) / 10**9
    
    print(f"\n状态 [{account_info}]")
    print(f"完整地址: {bot.address}")
    print(f"INI余额: {ini_balance:.6f}")
    print(f"USDT余额: {usdt_balance:.6f}")
    print(f"Gas价格: {gas_price:.2f} Gwei")
    print(f"签到估算费用: {checkin_fee:.6f} INI")
    print(f"兑换估算费用: {swap_fee:.6f} INI")
    
    print(f"\n最近的交易历史 [{account_info}]:")
    try:
        # 获取最近100个区块
        latest = w3.eth.block_number
        start_block = max(0, latest - 100)
        
        # 获取交易
        for block in range(latest, start_block, -1):
            block_data = w3.eth.get_block(block, True)
            
            for tx in block_data.transactions:
                if tx['from'].lower() == bot.address.lower() or (tx['to'] and tx['to'].lower() == bot.address.lower()):
                    # 获取时间戳
                    timestamp = datetime.fromtimestamp(block_data.timestamp, wib)
                    
                    # 确定交易类型
                    tx_type = "未知"
                    if tx['to'] and tx['to'].lower() == DAILY_CHECKIN_CONTRACT.lower():
                        tx_type = "每日签到"
                    elif tx['to'] and tx['to'].lower() == ROUTER_CONTRACT.lower():
                        tx_type = "兑换"
                        
                    print(f"区块 {block} ({timestamp:%Y-%m-%d %H:%M:%S}) - {tx_type} (Gas: {tx['gas']})")
                    print(f"  哈希: {tx['hash'].hex()}")
                    
    except Exception as e:
        print(f"获取交易历史时出错: {str(e)}")
    
    print("\n过程完成!")

def process_accounts(private_keys, action):
    """处理多个账户"""
    for i, private_key in enumerate(private_keys, 1):
        bot = IniChainBot(private_key)
        account_info = f"账户 {i} | {bot.address[-4:]}"
        if action == "checkin":
            bot.daily_checkin(account_info)
        elif action == "swap":
            bot.perform_swap(account_info)
        elif action == "status":
            show_status(private_key, i)
        time.sleep(5)  # 账户之间的延迟

def auto_daily_and_swap(private_keys):
    """自动每日签到和兑换，循环执行"""
    cycle_count = 1
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"开始第 {cycle_count} 个周期...")
            print(f"{'='*50}")
            
            # 执行每日签到
            print("\n开始每日签到...")
            process_accounts(private_keys, "checkin")
            print("每日签到完成!")
            
            # 等待5秒后开始兑换
            print("\n等待5秒后开始兑换...")
            time.sleep(5)
            
            # 执行兑换
            print("\n开始兑换过程...")
            process_accounts(private_keys, "swap")
            print("兑换过程完成!")
    
            # 等待5秒后发送INI到自身
            print("\n等待5秒后开始发送INI到自身...")
            time.sleep(5)
            
            # 执行发送INI到自身
            print("\n开始发送INI到自身的过程...")
            send_ini_to_self(private_keys)
            print("发送INI到自身的过程完成!")
            
            print(f"\n第 {cycle_count} 个周期完成")
            print("等待10分钟后开始下一个周期...")
            
            # 倒计时
            for i in range(600, 0, -1):  # 600秒 = 10分钟
                minutes = i // 60
                seconds = i % 60
                print(f"\r下一个周期开始的时间: {minutes:02d}:{seconds:02d}", end="")
                time.sleep(1)
            
            print("\n")  # 倒计时结束后的换行
            cycle_count += 1
            
        except KeyboardInterrupt:
            print("\n停止自动每日签到和兑换...")
            break
        except Exception as e:
            print(f"\n周期中出错: {str(e)}")
            print("尝试继续下一个周期...")
            time.sleep(10)

def cycle_send_ini_to_self(private_keys):
    """每20-30秒随机发送INI到自身地址"""
    print("\n=== 开始循环转账 ===")
    cycle_count = 0
    pending_txs = []
    nonce_tracker = {}  # 跟踪每个地址的nonce
    MIN_INTERVAL = 20
    MAX_INTERVAL = 30

    try:
        while True:
            cycle_start_time = time.time()
            
            for i, private_key in enumerate(private_keys, 1):
                try:
                    bot = IniChainBot(private_key)
                    account_info = f"账户 {i} | {bot.address[-4:]}"
                    
                    # 获取或更新nonce
                    current_nonce = w3.eth.get_transaction_count(bot.address)
                    nonce_tracker[bot.address] = max(
                        current_nonce,
                        nonce_tracker.get(bot.address, current_nonce)
                    )
                    
                    balance = w3.eth.get_balance(bot.address)
                    formatted_balance = w3.from_wei(balance, 'ether')
                    
                    gas_price = w3.eth.gas_price
                    gas_price = int(gas_price * 1.1)  # 增加10%的gas价格
                    estimated_gas = 21000
                    gas_cost = gas_price * estimated_gas
                    safe_balance = balance - gas_cost
                    
                    if safe_balance <= 0:
                        print(f"[{account_info}] 余额不足")
                        continue
                    
                    percentage = random.uniform(0.03, 0.05)
                    amount_to_send = int(safe_balance * percentage)
                    
                    if amount_to_send <= 0:
                        print(f"[{account_info}] 转账金额过小")
                        continue
                    
                    print(f"\n[{account_info}] 发送新交易...")
                    print(f"[{account_info}] 当前余额: {formatted_balance:.6f} INI")
                    print(f"[{account_info}] 转账金额: {w3.from_wei(amount_to_send, 'ether'):.6f} INI ({percentage*100:.2f}%)")
                    print(f"[{account_info}] Gas价格: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
                    print(f"[{account_info}] Nonce: {nonce_tracker[bot.address]}")
                    
                    transaction = {
                        'nonce': nonce_tracker[bot.address],
                        'gasPrice': gas_price,
                        'gas': estimated_gas,
                        'to': bot.address,
                        'value': amount_to_send,
                        'chainId': CHAIN_ID,
                        'data': '0x'
                    }
                    
                    signed = w3.eth.account.sign_transaction(transaction, private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                    
                    # 增加nonce，为下一笔交易准备
                    nonce_tracker[bot.address] += 1
                    
                    pending_txs.append({
                        'hash': tx_hash,
                        'account_info': account_info,
                        'time': time.time()
                    })
                    
                    print(f"[{account_info}] 交易已发送: {tx_hash.hex()}")
                    
                except Exception as e:
                    print(f"[{account_info}] 发送交易出错: {str(e)}")
                    # 发生错误时重置nonce
                    if bot.address in nonce_tracker:
                        del nonce_tracker[bot.address]
                
                time.sleep(1)
            
            # 检查待确认的交易
            for tx in pending_txs[:]:
                try:
                    receipt = w3.eth.get_transaction_receipt(tx['hash'])
                    if receipt:
                        if receipt['status'] == 1:
                            print(f"[{tx['account_info']}] 交易确认成功: {tx['hash'].hex()}")
                            cycle_count += 1
                        else:
                            print(f"[{tx['account_info']}] 交易失败: {tx['hash'].hex()}")
                        pending_txs.remove(tx)
                except Exception:
                    if time.time() - tx['time'] > 300:  # 5分钟超时
                        print(f"[{tx['account_info']}] 交易超时: {tx['hash'].hex()}")
                        pending_txs.remove(tx)
            
            print(f"\n当前成功次数: {cycle_count}")
            print(f"待确认交易数: {len(pending_txs)}")
            
            # 随机等待20-30秒
            elapsed = time.time() - cycle_start_time
            interval = random.uniform(MIN_INTERVAL, MAX_INTERVAL)
            if elapsed < interval:
                wait_time = interval - elapsed
                print(f"\n等待下一次转账... ({int(wait_time)} 秒)")
                time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n停止转账...")
        print(f"总成功次数: {cycle_count}")
        if pending_txs:
            print(f"还有 {len(pending_txs)} 笔交易待确认")

def show_menu():
    """显示主菜单"""
    print("\n=== INI Chain 机器人 ===")
    print("1. 查看账户状态")
    print("2. 每日签到")
    print("3. 循环兑换")
    print("4. 创建代币")
    print("5. 自动每日签到与兑换")
    print("6. 循环发送INI到自身 (每20-30秒)")
    print("7. 退出")
    return input("\n请选择功能 (1-7): ")

def cycle_swap(private_keys):
    """每10分钟执行一次兑换循环"""
    cycle_count = 1
    while True:
        try:
            print(f"\n开始第 {cycle_count} 个兑换周期...")
            process_accounts(private_keys, "swap")
            print(f"\n第 {cycle_count} 个兑换周期完成")
            print("等待10分钟后开始下一个周期...")
            
            # 倒计时
            for i in range(600, 0, -1):  # 600秒 = 10分钟
                minutes = i // 60
                seconds = i % 60
                print(f"\r下一个兑换周期开始的时间: {minutes:02d}:{seconds:02d}", end="")
                time.sleep(1)
            
            print("\n")  # 倒计时结束后的换行
            cycle_count += 1
            
        except KeyboardInterrupt:
            print("\n停止兑换周期...")
            break
        except Exception as e:
            print(f"\n兑换周期中出错: {str(e)}")
            print("尝试继续下一个周期...")
            time.sleep(10)

def send_ini_to_self(private_keys):
    """向自身地址发送INI，金额为余额的3-5%"""
    for i, private_key in enumerate(private_keys, 1):
        try:
            bot = IniChainBot(private_key)
            account_info = f"账户 {i} | {bot.address[-4:]}"
            
            # 获取当前余额
            balance = w3.eth.get_balance(bot.address)
            formatted_balance = w3.from_wei(balance, 'ether')
            
            # 计算安全Gas费用
            gas_price = bot.get_gas_price()
            estimated_gas = 21000  # 转账的标准Gas
            gas_cost = gas_price * estimated_gas
            
            # 计算安全余额（余额 - Gas费用）
            safe_balance = balance - gas_cost
            
            if safe_balance <= 0:
                print(f"[{account_info}] 余额不足以进行转账")
                print(f"[{account_info}] 当前余额: {formatted_balance:.6f} INI")
                print(f"[{account_info}] 估算Gas费用: {w3.from_wei(gas_cost, 'ether'):.6f} INI")
                continue
            
            # 计算随机金额，介于余额的3-5%
            percentage = random.uniform(0.03, 0.05)
            amount_to_send = int(safe_balance * percentage)
            
            if amount_to_send <= 0:
                print(f"[{account_info}] 转账金额过小")
                continue
            
            print(f"\n[{account_info}] 开始向自身转账INI...")
            print(f"[{account_info}] 当前余额: {formatted_balance:.6f} INI")
            print(f"[{account_info}] 转账金额: {w3.from_wei(amount_to_send, 'ether'):.6f} INI ({percentage*100:.2f}%)")
            print(f"[{account_info}] Gas价格: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
            
            # 构建交易
            transaction = {
                'from': bot.address,
                'to': bot.address,
                'value': amount_to_send,
                'gas': estimated_gas,
                'gasPrice': gas_price,
                'nonce': w3.eth.get_transaction_count(bot.address),
                'chainId': CHAIN_ID
            }
            
            # 签名并发送交易
            signed_txn = w3.eth.account.sign_transaction(transaction, bot.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # 等待交易回执
            receipt = bot.wait_for_transaction(tx_hash)
            
            if receipt and receipt['status'] == 1:
                print(f"[{account_info}] 转账成功!")
                print(f"[{account_info}] 交易哈希: {tx_hash.hex()}")
            else:
                print(f"[{account_info}] 转账失败!")
                
        except Exception as e:
            print(f"[{account_info}] 出错: {str(e)}")
        
        # 账户之间的延迟
        time.sleep(5)

def main():
    # 加载私钥
    try:
        with open("privatekey.txt", "r") as f:
            private_keys = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("错误: 找不到文件 privatekey.txt!")
        return
        
    while True:
        choice = show_menu()
        
        if choice == "1":
            process_accounts(private_keys, "status")
        elif choice == "2":
            process_accounts(private_keys, "checkin")
        elif choice == "3":
            cycle_swap(private_keys)
        elif choice == "4":
            # 创建代币菜单
            print("\n=== 创建代币 ===")
            name = input("代币全名: ")
            symbol = input("代币简称: ")
            try:
                total_supply = float(input("发行代币数量: "))
                decimals = int(input("代币小数位数 (默认18): ") or "18")
            except ValueError:
                print("错误: 代币数量或小数位数输入无效!")
                continue
                
            # 为每个私钥处理创建代币
            for i, private_key in enumerate(private_keys, 1):
                bot = IniChainBot(private_key)
                account_info = f"账户 #{i}"
                bot.create_token(name, symbol, total_supply, decimals, account_info)
        elif choice == "5":
            print("\n=== 自动每日签到与兑换 ===")
            print("机器人将自动执行每日签到和兑换")
            print("按 Ctrl+C 停止")
            auto_daily_and_swap(private_keys)
        elif choice == "6":
            print("\n=== 循环发送INI到自身 ===")
            print("机器人将每20-30秒随机发送余额的3-5% INI到自身地址")
            print("按 Ctrl+C 停止")
            cycle_send_ini_to_self(private_keys)
        elif choice == "7":
            print("\n感谢您使用机器人!")
            break
        else:
            print("\n无效的选择!")

if __name__ == "__main__":
    main()
