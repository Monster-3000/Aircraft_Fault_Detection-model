import cv2
import numpy as np
from pytorch_grad_cam import EigenCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from ultralytics.nn.tasks import DetectionModel

class YOLOv8Target:
    def __init__(self, m):
        self.m = m
    def __call__(self, x):
        return self.m(x)[0]

class ExplainerService:
    def __init__(self, model):
        self.model = model
        
        # YOLOv8 models usually have the DetectionModel in model.model
        if hasattr(self.model, "model") and isinstance(self.model.model, DetectionModel):
            # We target the last convolution layer before detection head
            target_layers = [self.model.model.model[-2]]
        else:
            raise ValueError("Unsupported YOLO model architecture for XAI")
            
        self.cam = EigenCAM(self.model.model, target_layers)

    def generate_heatmap(self, image_path: str, output_path: str):
        """
        Generates an Eigen-CAM heatmap for the image and saves it to output_path.
        """
        # Read the image
        img = cv2.imread(image_path)
        img = cv2.resize(img, (640, 640))
        rgb_img = img[:, :, ::-1] / 255.0
        
        # Prepare input tensor for CAM
        tensor = self.model.predictor.preprocess([img]) if hasattr(self.model, 'predictor') and self.model.predictor else None
        
        # Fallback if predictor is not initialized
        if tensor is None:
            import torch
            tensor = torch.from_numpy(img).float().permute(2, 0, 1).unsqueeze(0) / 255.0
            tensor = torch.nn.functional.interpolate(tensor, size=(640, 640))
            if next(self.model.model.parameters()).is_cuda:
                tensor = tensor.cuda()

        # Generate CAM
        grayscale_cam = self.cam(input_tensor=tensor, targets=[])
        grayscale_cam = grayscale_cam[0, :]
        
        # Ensure sizes match
        if grayscale_cam.shape != rgb_img.shape[:2]:
            grayscale_cam = cv2.resize(grayscale_cam, (rgb_img.shape[1], rgb_img.shape[0]))
        
        # Overlay on original image
        cam_image = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)
        cam_image = cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR)
        
        # Save
        cv2.imwrite(output_path, cam_image)
        return output_path
