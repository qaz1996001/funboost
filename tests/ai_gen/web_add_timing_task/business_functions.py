"""
Business functions module for timing tasks
Defines all business functions that need to be called on a schedule
"""
import time
from datetime import datetime
from funboost import boost, BrokerEnum


# Define business functions using the funboost decorator
@boost('task_queue', broker_kind=BrokerEnum.REDIS)
def send_email_task(to_email: str, subject: str, content: str):
    """Send email task"""
    print(f"[{datetime.now()}] Starting to send email")
    print(f"Recipient: {to_email}")
    print(f"Subject: {subject}")
    print(f"Content: {content}")

    # Simulate the time-consuming operation of sending an email
    time.sleep(2)

    print(f"[{datetime.now()}] Email sent successfully")
    return {"status": "success", "message": "Email sent successfully"}


@boost('data_sync_queue', broker_kind=BrokerEnum.REDIS)
def data_sync_task(source_db: str, target_db: str, table_name: str):
    """Data sync task"""
    print(f"[{datetime.now()}] Starting data sync")
    print(f"Source database: {source_db}")
    print(f"Target database: {target_db}")
    print(f"Table name: {table_name}")

    # Simulate data sync operation
    time.sleep(3)

    print(f"[{datetime.now()}] Data sync complete")
    return {"status": "success", "message": f"Table {table_name} sync complete"}


@boost('report_queue', broker_kind=BrokerEnum.REDIS)
def generate_report_task(report_type: str, date_range: str):
    """Generate report task"""
    print(f"[{datetime.now()}] Starting to generate report")
    print(f"Report type: {report_type}")
    print(f"Date range: {date_range}")

    # Simulate report generation
    time.sleep(5)

    print(f"[{datetime.now()}] Report generation complete")
    return {"status": "success", "message": f"{report_type} report generation complete"}


@boost('cleanup_queue', broker_kind=BrokerEnum.REDIS)
def cleanup_temp_files_task(directory: str, days_old: int):
    """Clean up temporary files task"""
    print(f"[{datetime.now()}] Starting to clean up temporary files")
    print(f"Directory: {directory}")
    print(f"Cleaning files older than {days_old} days")

    # Simulate cleanup operation
    time.sleep(1)

    print(f"[{datetime.now()}] Temporary file cleanup complete")
    return {"status": "success", "message": f"Cleaned up files older than {days_old} days in directory {directory}"}


@boost('backup_queue', broker_kind=BrokerEnum.REDIS)
def database_backup_task(database_name: str, backup_path: str):
    """Database backup task"""
    print(f"[{datetime.now()}] Starting database backup")
    print(f"Database: {database_name}")
    print(f"Backup path: {backup_path}")

    # Simulate backup operation
    time.sleep(4)

    print(f"[{datetime.now()}] Database backup complete")
    return {"status": "success", "message": f"Database {database_name} backup complete"}
