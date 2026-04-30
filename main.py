import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7860,
        reload=True,
        reload_dirs=["app"],
        reload_excludes=["*.db", "*.db-journal", "*.db-wal", "*.db-shm"],
    )
