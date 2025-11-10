"""
SFT（监督微调）训练器：使用LoRA进行高效微调
"""
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
from typing import Dict, List
from app.config import settings
import os


class SFTTrainer:
    """SFT训练器：实现监督微调"""

    def __init__(self, base_model: str = "Qwen/Qwen2-1.5B"):
        """
        初始化SFT训练器

        Args:
            base_model: 基础模型名称
        """
        self.base_model = base_model
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_model(self):
        """加载模型和tokenizer"""
        print(f"加载模型: {self.base_model}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model,
            trust_remote_code=True
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )

        # 配置LoRA
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,  # LoRA rank
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj"]  # 根据模型结构调整
        )

        self.model = get_peft_model(self.model, lora_config)
        print(f"模型已加载到设备: {self.device}")

    def prepare_dataset(self, data: List[Dict]) -> Dataset:
        """
        准备训练数据集

        Args:
            data: 训练数据列表，格式：[{"prompt": "...", "response": "..."}, ...]

        Returns:
            Dataset对象
        """

        def tokenize_function(examples):
            # 组合prompt和response
            texts = [
                f"### 提示词:\n{item['prompt']}\n### 回答:\n{item['response']}"
                for item in examples
            ]
            return self.tokenizer(texts, truncation=True, max_length=512, padding=True)

        dataset = Dataset.from_list(data)
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        return tokenized_dataset

    def train(self, train_data: List[Dict], output_dir: str = None):
        """
        执行训练

        Args:
            train_data: 训练数据
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = os.path.join(settings.MODEL_PATH, "sft_model")

        os.makedirs(output_dir, exist_ok=True)

        # 准备数据集
        dataset = self.prepare_dataset(train_data)

        # 训练参数
        training_args = TrainingArguments(
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
            report_to="none"
        )

        # 数据整理器
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )

        # 创建训练器
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator
        )

        # 开始训练
        print("开始SFT训练...")
        trainer.train()

        # 保存模型
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        print(f"模型已保存到: {output_dir}")

    def generate(self, prompt: str, max_length: int = 200) -> str:
        """
        使用训练后的模型生成文本

        Args:
            prompt: 输入提示词
            max_length: 最大长度

        Returns:
            生成的文本
        """
        if self.model is None or self.tokenizer is None:
            raise ValueError("模型未加载，请先调用load_model()")

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=0.7,
                do_sample=True
            )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)