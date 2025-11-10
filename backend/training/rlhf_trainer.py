"""
RLHF训练器：实现强化学习人类反馈优化
使用DPO（Direct Preference Optimization）方法
"""
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments
)
from trl import DPOTrainer, DPOTrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
from typing import List, Dict
from app.config import settings
import os


class RLHFTrainer:
    """RLHF训练器：实现DPO训练"""

    def __init__(self, base_model: str = "Qwen/Qwen2-1.5B"):
        """
        初始化RLHF训练器

        Args:
            base_model: 基础模型名称
        """
        self.base_model = base_model
        self.tokenizer = None
        self.model = None
        self.ref_model = None  # 参考模型
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_model(self):
        """加载模型"""
        print(f"加载模型: {self.base_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            trust_remote_code=True
        )

        # 加载主模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )

        # 配置LoRA
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj"]
        )
        self.model = get_peft_model(self.model, lora_config)

        # 加载参考模型（用于DPO）
        self.ref_model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        self.ref_model = get_peft_model(self.ref_model, lora_config)

        print(f"模型已加载到设备: {self.device}")

    def prepare_preference_dataset(self, data: List[Dict]) -> Dataset:
        """
        准备偏好数据集

        Args:
            data: 偏好数据，格式：[{
                "prompt": "...",
                "chosen": "更好的回答",
                "rejected": "较差的回答"
            }, ...]

        Returns:
            Dataset对象
        """
        # 转换数据格式
        processed_data = []
        for item in data:
            processed_data.append({
                "prompt": item["prompt"],
                "chosen": item["chosen"],
                "rejected": item["rejected"]
            })

        return Dataset.from_list(processed_data)

    def train(self, train_data: List[Dict], output_dir: str = None):
        """
        执行DPO训练

        Args:
            train_data: 训练数据
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = os.path.join(settings.MODEL_PATH, "rlhf_model")

        os.makedirs(output_dir, exist_ok=True)

        # 准备数据集
        dataset = self.prepare_preference_dataset(train_data)

        # DPO训练参数
        training_args = DPOTrainingArguments(
            output_dir=output_dir,
            num_train_epochs=settings.EPOCHS,
            per_device_train_batch_size=settings.BATCH_SIZE,
            gradient_accumulation_steps=4,
            learning_rate=settings.LEARNING_RATE,
            fp16=torch.cuda.is_available(),
            logging_steps=10,
            save_steps=100,
            save_total_limit=3,
            warmup_steps=50,
            report_to="none",
            beta=0.1  # DPO beta参数
        )

        # 创建DPO训练器
        trainer = DPOTrainer(
            model=self.model,
            ref_model=self.ref_model,
            args=training_args,
            train_dataset=dataset,
            tokenizer=self.tokenizer,
            beta=0.1
        )

        # 开始训练
        print("开始RLHF训练...")
        trainer.train()

        # 保存模型
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        print(f"模型已保存到: {output_dir}")