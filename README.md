# Tennis Vision

Automated tennis video analysis — tracks players and ball, overlays stats, and generates a shot heatmap.

## Running the App

### 1. SSH into the cluster

```bash
[ssh into cluster command]
```

### 2. Allocate a compute node

```bash
[allocate node and cd]
```

Note the hostname of the node:

```bash
hostname
# e.g. node042
```

### 3. Start the backend

```bash
cd tennis-vision
uvicorn backend.app:app --host 0.0.0.0 --port 8080
```

### 4. Open an SSH tunnel (on your laptop, in a separate terminal)

```bash
ssh -L 8080:node042:8080 [ssh into cluster command]
```

Replace `node042` with the hostname from step 2.

### 5. Open the app

Go to **http://localhost:8080** in your browser.
