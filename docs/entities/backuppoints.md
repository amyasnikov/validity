# Backup Points

If a [Data Source](https://netboxlabs.com/docs/netbox/en/stable/models/core/datasource/) is used to download data to NetBox, **Backup Point** solves the opposite task, it can **upload** data source contents to some external storage. This is mostly suitable for performing [device configuration backup](../features/config_backup.md).

Currently **Git** and **AWS S3** backup methods are available.

## Fields

#### Name
The Name of the Backup Point. Must be unique.

#### Data Source
Data Source which is going to be backed up. Only Data Sources with  the type [device_polling](datasources.md) are allowed to be used here.

#### Back Up After Sync
If this param is `True`, backup will be performed each time respective Data Source is synced. For instance, you press "Sync" button on the Data Source page, sync is performed and after that Data Source contents are uploaded to the destination(s) specified in all bound Backup Points.

#### Method
Defines protocol for uploading the Data Source.

Available options are:
* Git (over http(s))
* Amazon S3 (or any other S3-compatible service)

#### URL
URL of the endpoint where the Data Source contents will be uploaded.

Examples of the URLs:

| Method        | Example URL                                                |
|---------------|------------------------------------------------------------|
| Git           | `https://github.com/amyasnikov/my_awesome_repo`            |
| S3 no-archive | `https://s3.eu-north-1.amazonaws.com/bucket_name/folder`   |
| S3 archive    | `https://s3.eu-north-1.amazonaws.com/bucket_name/arch.zip` |


#### Ignore Rules
A set of rules (one per line) identifying filenames to ignore during Data Source backup. Some examples are provided below. See Python's [fnmatch()](https://docs.python.org/3/library/fnmatch.html) documentation for a complete reference.

| Rule               | Description                                                  |
|--------------------|--------------------------------------------------------------|
| `folder/file.json` | Do not back up one specific file                             |
| `*.txt`            | Do not back up all files with **txt** extension              |
| `router-??.txt`    | Do not back up files like `router-11.txt` and `router-ab.txt` |


#### Git-specific parameters
* **Username**, **Password** - credentials to perform HTTP authentication, and access the repository
* **Branch** - git branch. Default repository branch will be used if the field is empty

#### S3-specific parameters
* **AWS access key ID**, **AWS secret access key** - credentials to perform authentication in S3 service
* **archive** - if this field is True, Data Source contents will be packed into ZIP archive and then uploaded
