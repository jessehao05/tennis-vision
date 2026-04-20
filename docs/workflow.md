# Development Workflow

## One-Time Setup (Cluster)

1. SSH into login node:

   ```bash
   ssh haojz@login.accre.vu
   ```

2. Allocate a GPU node and SSH into it:

   ```bash
   salloc --account=es3890_acc --partition=batch_gpu --gres=gpu:nvidia_rtx_a6000:1 --time=01:00:00 --mem=48G
   ssh <nodename>
   ```

3. Load software stack and modules:

   ```bash
   setup_accre_software_stack
   module load python/3.12.4 scipy-stack/2025a
   module load gcc opencv
   ```

4. Create and activate virtual environment:

   ```bash
   cd tennis-vision
   python -m venv .venv
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   pip install ultralytics torch torchvision uvicorn fastapi python-multipart opencv-python
   pip install lap
   ```

6. Build the frontend (run on local machine, then push):

   ```bash
   cd frontend
   npm install
   npm run build
   git add frontend/dist
   git commit -m "build frontend"
   git push
   ```

7. Pull on the cluster:
   ```bash
   git pull
   ```

---

## Every Session

### Terminal 1 — Cluster (backend)

1. SSH into login node:

   ```bash
   ssh haojz@login.accre.vu
   ```

2. Allocate a GPU node, SSH into it, and note the hostname:

   ```bash
   salloc --account=es3890_acc --partition=batch_gpu --gres=gpu:nvidia_rtx_a6000:1 --time=01:00:00 --mem=48G
   ssh <nodename>
   hostname
   # e.g. gpu0203 — you will need this value for the SSH tunnel in Terminal 2
   ```

3. Load modules and activate venv:

   ```bash
   setup_accre_software_stack
   module load python/3.12.4 scipy-stack/2025a
   module load gcc opencv
   cd tennis-vision
   source .venv/bin/activate
   ```

4. Start the backend:
   ```bash
   python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080
   ```

### Terminal 2 — Local machine (SSH tunnel)

```bash
ssh -L 8080:<nodename>:8080 haojz@login.accre.vu
```

Replace `<nodename>` with the hostname from step 2 above (e.g. `gpu0203`).

### Browser

Go to **http://localhost:8080**
