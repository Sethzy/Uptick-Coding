# 📊 CSV Configuration Guide - Uptick Crawler

The crawler now supports flexible CSV input configuration without hardcoded file paths.

## 🔧 **Current Configuration**

The crawler reads CSV configuration from `config.json`:

```json
{
  "csv_input": {
    "default_file": "../uptick-csvs/enriched-hubspot-TAM-08-25.csv",
    "domain_column": "tam_site",
    "id_column": "Record ID"
  }
}
```

## 🚀 **Quick Configuration Updates**

### **Option 1: Shell Script (Recommended)**

```bash
# Show current configuration
./update_csv.sh --show

# Update CSV file path
./update_csv.sh --file ../new_domains.csv

# Update domain column name
./update_csv.sh --domain-column website

# Update ID column name  
./update_csv.sh --id-column id

# Show help
./update_csv.sh --help
```

### **Option 2: Python Script**

```bash
# Show current configuration
python3 update_csv_config.py --show

# Update CSV file path
python3 update_csv_config.py --csv-file ../new_domains.csv

# Update domain column name
python3 update_csv_config.py --domain-column website

# Update ID column name
python3 update_csv_config.py --id-column id
```

### **Option 3: Manual Edit**

Edit `config.json` directly:

```json
{
  "csv_input": {
    "default_file": "path/to/your/domains.csv",
    "domain_column": "your_domain_column",
    "id_column": "your_id_column"
  }
}
```

## 📋 **CSV File Requirements**

Your CSV file must contain:

1. **Domain Column**: Contains website URLs/domains (e.g., `tam_site`, `website`, `domain`)
2. **ID Column**: Contains unique record identifiers (e.g., `Record ID`, `id`, `uuid`)

### **Example CSV Structure**

```csv
Record ID,Company Name,tam_site,State,Industry
12345,Acme Corp,acme.com,CA,Technology
12346,Widget Inc,widget.com,NY,Manufacturing
```

## 🔄 **Workflow Examples**

### **Change to Different CSV File**

```bash
# 1. Update configuration
./update_csv.sh --file ../uptick-csvs/new_domains.csv

# 2. Run crawler (uses new file automatically)
python3 run_crawl.py

# 3. Or override with CLI flag
python3 run_crawl.py --input-csv ../custom/domains.csv
```

### **Use Different Column Names**

```bash
# 1. Update column configuration
./update_csv.sh --domain-column website --id-column uuid

# 2. Run crawler (uses new columns automatically)
python3 run_crawl.py

# 3. Or override with CLI flags
python3 run_crawl.py --column website --id-column uuid
```

## 🎯 **CLI Override Options**

Even with configuration set, you can override via CLI:

```bash
# Override CSV file
python3 run_crawl.py --input-csv custom_domains.csv

# Override domain column
python3 run_crawl.py --column website

# Override ID column
python3 run_crawl.py --id-column id

# Combine overrides
python3 run_crawl.py --input-csv new.csv --column domain --id-column record_id
```

## 📁 **File Path Examples**

### **Relative Paths**
```bash
./update_csv.sh --file ../data/domains.csv
./update_csv.sh --file ../../uptick-csvs/domains.csv
./update_csv.sh --file domains.csv
```

### **Absolute Paths**
```bash
./update_csv.sh --file /Users/username/Projects/domains.csv
./update_csv.sh --file /home/user/data/domains.csv
```

## 🔍 **Troubleshooting**

### **Check Current Configuration**
```bash
./update_csv.sh --show
```

### **Verify CSV File Exists**
```bash
ls -la ../uptick-csvs/
```

### **Test CSV Loading**
```bash
# Run crawler with --dry-run to test configuration
python3 run_crawl.py --dry-run
```

### **Common Issues**

1. **File Not Found**: Check the path in `config.json`
2. **Column Not Found**: Verify column names exist in your CSV
3. **Permission Denied**: Ensure you have read access to the CSV file

## 📚 **Integration with Scoring**

After crawling, the scoring system can enrich the data:

```bash
# 1. Crawl domains (uses config from config.json)
cd crawler
python3 run_crawl.py

# 2. Enrich with HubSpot data
cd ../scoring
python3 -m scoring.quick_start enrich ../llm-input.jsonl ../uptick-csvs/enriched-hubspot-TAM-08-25.csv

# 3. Score enriched data
python3 -m scoring.quick_start score ../llm-input_enriched.jsonl
```

## 🎉 **Benefits of New System**

- ✅ **No hardcoded file paths** - Easy to switch between different CSV files
- ✅ **Centralized configuration** - All settings in one place
- ✅ **CLI overrides** - Flexible for different use cases
- ✅ **Easy updates** - Simple commands to change configuration
- ✅ **Backward compatible** - Existing workflows still work
- ✅ **Better logging** - See exactly what configuration is being used

---

**Need Help?** Run `./update_csv.sh --help` for usage examples!
