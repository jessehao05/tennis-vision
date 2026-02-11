from ultralytics import YOLO

model = YOLO("yolov8n.pt")

results = model("__", save=True)

# show results
for r in results:
    print(r.boxes.cls)