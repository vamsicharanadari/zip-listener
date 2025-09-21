# Product Requirements Document (PRD)

**Project Title:** Automated Folder Listener & ZIP Extractor  
**Author:** Vamsi Charan Adari
**Date:** 2025-09-20  
**Version:** 2.0  

---

## 1. Objective  
Create a Windows-based background process (Docker container) that continuously monitors a specified folder for incoming `.zip` files. Whenever a `.zip` file appears:  

- Automatically extract its contents into a **folder named after the `.zip` file**.  
- Move the extracted folder into a target destination folder.  
- **Delete the `.zip` file after successful extraction.**  
- Handle deletion errors gracefully (e.g., if the file is locked).  
- Keep running persistently using **periodic polling**, compatible with Windows Docker bind mounts.  

---

## 2. Scope  

### In Scope  
- Monitor a **source folder** continuously using **periodic polling**.  
- Detect new `.zip` files immediately (polling interval configurable).  
- Extract contents of the `.zip` file into a folder named after the `.zip`.  
- Move the extracted folder to a **destination folder**.  
- **Delete original `.zip` file once extraction and moving is successful.**  
- Retry or log deletion errors if `.zip` cannot be deleted.  
- Process runs continuously until manually stopped.  

### Out of Scope  
- Monitoring file types other than `.zip`.  
- Handling password-protected `.zip` files.  
- Handling corrupted `.zip` files beyond logging and skipping.  
- Flattening folder structures inside the zip (now preserved).  

---

## 3. Functional Requirements  

1. **Folder Monitoring** – Process must continuously poll the source folder for new `.zip` files.  
2. **File Validation** – Only `.zip` files trigger processing.  
3. **Extraction Logic** – Each `.zip` is extracted into `DEST_DIR/<zip_name>/`. Folder structure inside `.zip` is preserved.  
4. **File Handling** – Delete `.zip` after success; retry if locked, log errors if deletion fails.  
5. **Continuous Operation** – Runs as a Docker container, compatible with Windows volumes.  

---

## 4. Non-Functional Requirements  

- Detect `.zip` files **within polling interval** (default 10 seconds).  
- Handle multiple `.zip` files concurrently.  
- Continue operation even if one file is corrupted.  
- Configurable paths, retry intervals, overwrite policy, and scan interval.  
- Runs on Windows 10 and above in Docker.  
- Logs both to file and console.  

---

## 5. User Stories  

- **As a user**, I want `.zip` files in my monitored folder to be automatically extracted into their own folder.  
- **As a user**, I want nested folders inside the `.zip` to be preserved.  
- **As a user**, I want the `.zip` file deleted after extraction.  
- **As a user**, I want the system to gracefully handle locked files.  
- **As a user**, I want multiple `.zip` files processed at the same time.  
- **As a user**, I want leftover `.zip` files processed automatically after downtime. 
- **As a user**, I want the process to run continuously in the background.  

---

## 6. Assumptions & Dependencies  

- `.zip` files will not be password protected.  
- Process has read/write/delete permissions.  
- Sufficient disk space is available.  
- File locks are temporary.  
- Docker Desktop has access to the host drives containing source/destination folders.  
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
    A[Start / Periodically Scan Source Folder] --> B[Detect .zip Files]
    B --> C{New zip file?}
    C -- No --> D[Wait for next scan]
    C -- Yes --> E[Extract .zip into DEST/<zip_name>/]
    E --> F[Delete original .zip file]
    F --> G{Deletion failed?}
    G -- No --> H[Success]
    G -- Yes --> I[Retry deletion after delay]
    I --> F
    I -- Retry limit reached --> J[Log error & Skip file]
    J --> H