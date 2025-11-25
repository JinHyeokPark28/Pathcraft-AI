"""
OpenAI GPT-3.5 Fine-tuning Script
Train a custom POE expert model
"""

import os
import json
import logging
from typing import Dict
import time

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai package not installed. Run: pip install openai")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIFineTuner:
    """Fine-tune GPT-3.5 for POE expertise"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            logger.error("OPENAI_API_KEY not found")
            logger.info("Set your API key: export OPENAI_API_KEY=sk-...")
            return

        if OPENAI_AVAILABLE:
            openai.api_key = self.api_key

    def validate_dataset(self, file_path: str) -> Dict:
        """Validate fine-tuning dataset"""
        logger.info(f"Validating dataset: {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset not found: {file_path}")

        # Count lines and check format
        line_count = 0
        errors = []

        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line_count += 1

                try:
                    data = json.loads(line)

                    # Check required fields
                    if 'messages' not in data:
                        errors.append(f"Line {i}: Missing 'messages' field")
                        continue

                    messages = data['messages']
                    if len(messages) != 3:
                        errors.append(f"Line {i}: Expected 3 messages, got {len(messages)}")

                    # Check roles
                    expected_roles = ['system', 'user', 'assistant']
                    actual_roles = [msg.get('role') for msg in messages]

                    if actual_roles != expected_roles:
                        errors.append(f"Line {i}: Invalid role sequence: {actual_roles}")

                except json.JSONDecodeError:
                    errors.append(f"Line {i}: Invalid JSON")

        logger.info(f"Dataset validation complete: {line_count} examples")

        if errors:
            logger.warning(f"Found {len(errors)} errors:")
            for error in errors[:10]:  # Show first 10 errors
                logger.warning(f"  {error}")

        return {
            'total_examples': line_count,
            'errors': errors,
            'is_valid': len(errors) == 0
        }

    def upload_dataset(self, file_path: str) -> str:
        """Upload dataset to OpenAI"""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI package not available")
            return None

        logger.info(f"Uploading dataset: {file_path}")

        try:
            with open(file_path, 'rb') as f:
                response = openai.File.create(
                    file=f,
                    purpose='fine-tune'
                )

            file_id = response['id']
            logger.info(f"Dataset uploaded: {file_id}")

            return file_id

        except Exception as e:
            logger.error(f"Failed to upload dataset: {e}")
            return None

    def create_finetune_job(self, file_id: str, model: str = "gpt-3.5-turbo") -> Dict:
        """Create fine-tuning job"""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI package not available")
            return None

        logger.info(f"Creating fine-tune job for model: {model}")

        try:
            response = openai.FineTuningJob.create(
                training_file=file_id,
                model=model,
                hyperparameters={
                    'n_epochs': 3  # Default: 3-4 epochs
                }
            )

            job_id = response['id']
            logger.info(f"Fine-tune job created: {job_id}")

            return {
                'job_id': job_id,
                'status': response['status'],
                'model': response['model']
            }

        except Exception as e:
            logger.error(f"Failed to create fine-tune job: {e}")
            return None

    def check_job_status(self, job_id: str) -> Dict:
        """Check fine-tuning job status"""
        if not OPENAI_AVAILABLE:
            return None

        try:
            response = openai.FineTuningJob.retrieve(job_id)

            return {
                'job_id': job_id,
                'status': response['status'],
                'fine_tuned_model': response.get('fine_tuned_model'),
                'trained_tokens': response.get('trained_tokens'),
                'error': response.get('error')
            }

        except Exception as e:
            logger.error(f"Failed to check job status: {e}")
            return None

    def wait_for_completion(self, job_id: str, check_interval: int = 60):
        """Wait for fine-tuning to complete"""
        logger.info(f"Waiting for fine-tune job to complete: {job_id}")

        while True:
            status = self.check_job_status(job_id)

            if not status:
                break

            logger.info(f"Status: {status['status']}")

            if status['status'] == 'succeeded':
                logger.info(f"Fine-tuning complete! Model: {status['fine_tuned_model']}")
                return status

            elif status['status'] in ['failed', 'cancelled']:
                logger.error(f"Fine-tuning failed: {status.get('error')}")
                return status

            # Wait before next check
            time.sleep(check_interval)

    def run_full_pipeline(self, dataset_path: str = "data/qa_dataset/finetuning_dataset.jsonl"):
        """Run complete fine-tuning pipeline"""
        logger.info("=" * 80)
        logger.info("OPENAI FINE-TUNING PIPELINE")
        logger.info("=" * 80)

        # Step 1: Validate dataset
        logger.info("\n[STEP 1] Validating dataset...")
        validation = self.validate_dataset(dataset_path)

        if not validation['is_valid']:
            logger.error("Dataset validation failed!")
            return None

        logger.info(f"Dataset is valid: {validation['total_examples']} examples")

        # Step 2: Upload dataset
        logger.info("\n[STEP 2] Uploading dataset...")
        file_id = self.upload_dataset(dataset_path)

        if not file_id:
            logger.error("Dataset upload failed!")
            return None

        # Step 3: Create fine-tune job
        logger.info("\n[STEP 3] Creating fine-tune job...")
        job_info = self.create_finetune_job(file_id)

        if not job_info:
            logger.error("Failed to create fine-tune job!")
            return None

        # Step 4: Wait for completion
        logger.info("\n[STEP 4] Waiting for fine-tuning to complete...")
        logger.info("This may take 1-2 hours depending on dataset size...")

        final_status = self.wait_for_completion(job_info['job_id'])

        if final_status and final_status['status'] == 'succeeded':
            logger.info("\n" + "=" * 80)
            logger.info("FINE-TUNING COMPLETE!")
            logger.info("=" * 80)
            logger.info(f"Fine-tuned model: {final_status['fine_tuned_model']}")
            logger.info(f"Trained tokens: {final_status.get('trained_tokens', 'N/A')}")
            logger.info("\nYou can now use this model in your application:")
            logger.info(f"  model='{final_status['fine_tuned_model']}'")
            logger.info("=" * 80)

        return final_status


def main():
    """Main execution"""
    finetuner = OpenAIFineTuner()

    # Check if API key is set
    if not finetuner.api_key:
        print("\nPlease set your OpenAI API key:")
        print("  export OPENAI_API_KEY=sk-your-key-here")
        return

    # Run full pipeline
    result = finetuner.run_full_pipeline()

    if result:
        # Save result
        output_file = 'data/qa_dataset/finetuning_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        print(f"\nResult saved to: {output_file}")


if __name__ == '__main__':
    main()
