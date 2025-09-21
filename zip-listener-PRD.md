# Product Requirements Document (PRD)

**Project Title:** Automated Folder Listener & ZIP Extractor  
**Author:** [Your Name]  
**Date:** [Today’s Date]  
**Version:** 2.0  

---

## 1. Objective  

Create a **Dockerized background service** that continuously monitors a specified folder for incoming `.zip` files. Whenever a `.zip` file appears:  

- Automatically extract its contents.  
- Move the extracted contents into a **destination folder**, flattening any nested folders.  
- **Delete the `.zip` file after successful extraction and transfer.**  
- Handle deletion errors gracefully (e.g., if the file is locked).  
- Run persistently in the background as a Docker container.  
- Automatically process any `.zip` files left in the monitored folder at startup (resilient to downtime).  
- Support concurrent processing of multiple `.zip` files.  

---

## 2. Scope  

### In Scope  

- Monitor a **source folder** continuously.  
- Detect new `.zip` files immediately upon arrival.  
- Extract contents of the `.zip` file.  
- Flatten folder structure: if the `.zip` contains a folder, its contents should be moved directly into the destination folder.  
- Move extracted contents to a **destination folder**.  
- **Delete original `.zip` file once extraction and moving is successful.**  
- Retry or log deletion errors if `.zip` cannot be deleted (e.g., locked by another process).  
- Process runs continuously until manually stopped or container shut down.  
- Support multiple `.zip` files being processed concurrently.  
- Process leftover `.zip` files present at container startup.  

### Out of Scope  

- Monitoring file types other than `.zip`.  
- Handling password-protected `.zip` files.  
- Handling severely corrupted `.zip` files (will log and skip).  
- Complex folder structures beyond one level of nesting.  

---

## 3. Functional Requirements  

1. **Folder Monitoring** – Dockerized process continuously watches the source folder.  
2. **Startup Scan** – Any `.zip` files present at container start are processed automatically.  
3. **File Validation** – Only `.zip` files trigger processing.  
4. **Extraction Logic** – Flatten folder structure if needed, move files to destination.  
5. **File Handling** – Delete `.zip` after success; retry if locked, log errors if deletion fails.  
6. **Concurrency** – Multiple `.zip` files can be processed simultaneously (configurable via `MAX_WORKERS`).  
7. **Continuous Operation** – Run as Docker container, restart on failure.  
8. **Graceful Shutdown** – Container handles SIGTERM/SIGINT signals, finishing ongoing `.zip` processing before exiting.  

---

## 4. Non-Functional Requirements  

- Detect `.zip` files within **2 seconds** of arrival.  
- Handle multiple `.zip` files concurrently.  
- Process `.zip` files left in the folder after downtime.  
- Continue operation even if one file is corrupted.  
- Configurable via **environment variables**:  
  - `SOURCE_DIR`  
  - `DEST_DIR`  
  - `RETRY_INTERVAL`  
  - `MAX_RETRIES`  
  - `OVERWRITE_POLICY`  
  - `MAX_WORKERS`  
- Runs inside Docker on **Windows 10+ or Linux hosts**.  
- Logs rotation with max size 5MB, 3 backups.  

---

## 5. User Stories  

- **As a user**, I want `.zip` files in my monitored folder to be automatically extracted.  
- **As a user**, I want nested folders inside the `.zip` to be flattened.  
- **As a user**, I want the `.zip` file deleted after extraction.  
- **As a user**, I want the system to gracefully handle locked files.  
- **As a user**, I want multiple `.zip` files processed at the same time.  
- **As a user**, I want leftover `.zip` files processed automatically after downtime.  
- **As a user**, I want the process to run continuously in the background inside Docker.  

---

## 6. Assumptions & Dependencies  

- `.zip` files will not be password protected.  
- Process has read/write/delete permissions.  
- Sufficient disk space is available.  
- File locks are temporary.  
- Docker and docker-compose are installed on the host machine.  
- Watchtower is optional for auto-updating the container.  

---

## 7. Success Metrics  

- **100% of `.zip` files** extracted, moved, and deleted within **10 seconds** (if not locked).  
- **All leftover `.zip` files** present at container startup are processed automatically.  
- **Multiple `.zip` files** can be processed concurrently with no missed files.  
- **0 manual interventions** during normal operation.  
- **Graceful shutdown** ensures no data loss during container stop or Watchtower updates.  
- **Logs created** for:  
  - Corrupted or unprocessable files  
  - Locked `.zip` files with retry attempts  
  - Deleted files or failures  
- **Docker container uptime**: container automatically restarts on failure.  
- **Auto-updates**: container image can be updated via Watchtower with zero lost `.zip` files.  

Optional metrics for high-volume environments:  
- Average processing time per `.zip` file under load.  
- Maximum concurrent `.zip` files processed (`MAX_WORKERS`) without errors.  
- Disk space utilization of temp extraction folders.  

---

## 8. Future Enhancements  

- Support for password-protected archives.  
- Support for `.rar`, `.7z`, etc.  
- GUI for configuration.  
- Monitoring dashboard.  
- Metrics/alerts for high-volume `.zip` processing.  

---

## 9. Process Flow (Mermaid Diagram)  

```mermaid
flowchart TD
    A[Start / Docker Container] --> B[Scan SOURCE_DIR for leftover .zip files]
    B --> C{Any leftover .zip files?}
    C -- Yes --> D[Submit .zip files to ThreadPool for processing]
    C -- No --> E[Start Watchdog Observer]
    D --> E

    E --> F[Detect New File in SOURCE_DIR]
    F --> G{Is file .zip?}
    G -- No --> H[Ignore file]
    G -- Yes --> I[Submit .zip file to ThreadPool for processing]

    subgraph ZipProcessing
        I --> J[Extract .zip contents to temp folder]
        J --> K[Flatten extracted files into DEST_DIR]
        K --> L[Delete original .zip file with retries if locked]
        L --> M{Deletion successful?}
        M -- Yes --> N[Log success]
        M -- No --> O[Log failure, skip file]
    end

    H --> E
    N --> E
    O --> E