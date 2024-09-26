import json
import pandas as pd
from itemadapter import ItemAdapter
import logging
from scrapy.utils.project import get_project_settings

class SavingPipeline:
    def __init__(self):
        self.output_format = get_project_settings().get('OUTPUT_FORMAT')
        self.chunk_size = get_project_settings().get('CHUNK_SIZE')
        self.current_chunk = []
        self.file_counter = 0

    def close_spider(self, spider):
        if self.current_chunk:
            self.save_chunk()
        spider.logger.info("Spider closed and final data chunk saved")
        print("Spider closed and final data chunk saved") 
        
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.current_chunk.append(adapter.asdict())
        if len(self.current_chunk) >= self.chunk_size:
            self.save_chunk()
        return item

    def save_chunk(self):
        self.file_counter += 1
        file_name = f'output_{self.file_counter}.{self.output_format}'

        if self.output_format == 'json':
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(self.current_chunk, f, ensure_ascii=False, indent=4)
        elif self.output_format == 'jsonlines':
            with open(file_name, 'w', encoding='utf-8') as f:
                for item in self.current_chunk:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        elif self.output_format == 'parquet':
            df = pd.DataFrame(self.current_chunk)
            df.to_parquet(file_name)

        self.current_chunk = []
        logging.info(f"Data chunk saved to {file_name}")
        print("Data chunk saved to {file_name}")

