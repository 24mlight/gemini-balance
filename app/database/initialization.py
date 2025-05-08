"""
数据库初始化模块
"""
from dotenv import dotenv_values

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database.connection import engine, Base
from app.database.models import Settings
from app.log.logger import get_database_logger
import os
from dotenv import set_key

logger = get_database_logger()


def create_tables():
    """
    创建数据库表
    """
    try:
        # 创建所有表
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise


def import_env_to_settings():
    """  
    将系统环境变量更新到.env文件中（覆盖已存在的值），然后将.env文件配置项导入到t_settings表中  
    """
    try:
        # 查找.env文件路径
        env_path = dotenv_values.find_dotenv()
        if not env_path:
            env_path = ".env"
            logger.info(
                f"No .env file found, will create a new one at {env_path}")

        # 获取.env文件中的所有配置项
        env_values = dotenv_values(env_path)

        # 更新.env文件，使用系统环境变量（覆盖已存在的值）
        updated = False
        for key, value in os.environ.items():
            # 只考虑在Settings类中定义的环境变量
            if hasattr(Settings, key):
                if key not in env_values or env_values[key] != value:
                    set_key(env_path, key, value)
                    env_values[key] = value
                    updated = True
                    logger.info(
                        f"Updated .env file with system environment variable: {key}")

        if updated:
            logger.info(".env file updated with system environment variables")

        # 重新读取.env文件，确保使用最新值
        env_values = dotenv_values(env_path)

        # 获取检查器
        inspector = inspect(engine)

        # 检查t_settings表是否存在
        if "t_settings" in inspector.get_table_names():
            # 使用Session进行数据库操作
            with Session(engine) as session:
                # 获取所有现有的配置项
                current_settings = {
                    setting.key: setting for setting in session.query(Settings).all()}

                # 遍历所有配置项
                for key, value in env_values.items():
                    if key in current_settings:
                        # 更新已存在的配置项
                        if current_settings[key].value != value:
                            current_settings[key].value = value
                            logger.info(f"Updated setting: {key}")
                    else:
                        # 插入新的配置项
                        new_setting = Settings(key=key, value=value)
                        session.add(new_setting)
                        logger.info(f"Inserted setting: {key}")

                # 提交事务
                session.commit()

        logger.info(
            "Environment variables imported to settings table successfully")
    except Exception as e:
        logger.error(
            f"Failed to import environment variables to settings table: {str(e)}")
        raise


def initialize_database():
    """
    初始化数据库
    """
    try:
        # 创建表
        create_tables()

        # 导入环境变量
        import_env_to_settings()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
