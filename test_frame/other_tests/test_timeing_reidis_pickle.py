
s1 = b'''
\x80\x04\x95W\x04\x00\x00\x00\x00\x00\x00}\x94(\x8C\x07version\x94K\x01\x8C\x02id\x94\x8C\x09cron_job1\x94\x8C\x04func\x94\x8C=funboost.timing_job.timing_job_base:push_fun_params_to_broker\x94\x8C\x07trigger\x94\x8C\x19apscheduler.triggers.cron\x94\x8C\x0BCronTrigger\x94\x93\x94)\x81\x94}\x94(h\x01K\x02\x8C\x08timezone\x94\x8C\x04pytz\x94\x8C\x02_p\x94\x93\x94(\x8C\x0DAsia/Shanghai\x94M\xE8qK\x00\x8C\x03LMT\x94t\x94R\x94\x8C\x0Astart_date\x94N\x8C\x08end_date\x94N\x8C\x06fields\x94]\x94(\x8C apscheduler.triggers.cron.fields\x94\x8C\x09BaseField\x94\x93\x94)\x81\x94}\x94(\x8C\x04name\x94\x8C\x04year\x94\x8C\x0Ais_default\x94\x88\x8C\x0Bexpressions\x94]\x94\x8C%apscheduler.triggers.cron.expressions\x94\x8C\x0DAllExpression\x94\x93\x94)\x81\x94}\x94\x8C\x04step\x94Nsbaubh\x18\x8C\x0AMonthField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8C\x05month\x94h\x1F\x88h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x18\x8C\x0FDayOfMonthField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8C\x03day\x94h\x1F\x88h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x18\x8C\x09WeekField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8C\x04week\x94h\x1F\x88h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x18\x8C\x0EDayOfWeekField\x94\x93\x94)\x81\x94}\x94(h\x1D\x8C\x0Bday_of_week\x94h\x1F\x89h ]\x94h$)\x81\x94}\x94h'Nsbaubh\x1A)\x81\x94}\x94(h\x1D\x8C\x04hour\x94h\x1F\x89h ]\x94h"\x8C\x0FRangeExpression\x94\x93\x94)\x81\x94}\x94(h'N\x8C\x05first\x94K\x17\x8C\x04last\x94K\x17ubaubh\x1A)\x81\x94}\x94(h\x1D\x8C\x06minute\x94h\x1F\x89h ]\x94hM)\x81\x94}\x94(h'NhPK1hQK1ubaubh\x1A)\x81\x94}\x94(h\x1D\x8C\x06second\x94h\x1F\x89h ]\x94hM)\x81\x94}\x94(h'NhPK2hQK2ubaube\x8C\x06jitter\x94Nub\x8C\x08executor\x94\x8C\x07default\x94\x8C\x04args\x94\x8C\x0Asum_queue3\x94\x85\x94\x8C\x06kwargs\x94}\x94(\x8C\x01x\x94K2\x8C\x01y\x94K<uh\x1D\x8C.push_fun_params_to_broker_for_queue_sum_queue3\x94\x8C\x12misfire_grace_time\x94K\x01\x8C\x08coalesce\x94\x88\x8C\x0Dmax_instances\x94K\x01\x8C\x0Dnext_run_time\x94\x8C\x08datetime\x94\x8C\x08datetime\x94\x93\x94C\x0A\x07\xE9\x06\x1A\x1712\x00\x00\x00\x94h\x0F(h\x10M\x80pK\x00\x8C\x03CST\x94t\x94R\x94\x86\x94R\x94u.
'''

import pickle

# Fix: Remove leading and trailing newlines and extra characters from binary data
# This is the main reason for deserialization failure
cleaned_data = s1.strip()

print(f"Original data length: {len(s1)}")
print(f"Cleaned data length: {len(cleaned_data)}")

try:
    job = pickle.loads(cleaned_data)
    print(job)
    print("✅ Deserialization successful!")
    print(f"Job ID: {job['id']}")
    print(f"Job function: {job['func']}")
    print(f"Job trigger: {job['trigger']}")
    print(f"Job parameters: args={job['args']}, kwargs={job['kwargs']}")
    print(f"Next run time: {job['next_run_time']}")

    # This is a dictionary representation of an APScheduler job
    print(f"\nJob type: {type(job)}")

except Exception as e:
    print(f"❌ Deserialization failed: {e}")
    print("Please ensure the data format is correct and check for extra characters")

print("\n=== Problem Summary ===")
print("""
Cause of APScheduler Redis serialization issue:
1. Binary data contains leading/trailing newlines \\n
2. pickle.loads() requires strict data format with no extra characters
3. Solution: Use data.strip() to clean the data

Prevention:
1. Ensure data format is correct when storing in Redis
2. Validate and clean data when reading
3. Use appropriate serialization configuration
""")