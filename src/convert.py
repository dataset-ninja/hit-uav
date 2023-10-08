import supervisely as sly
import os
from dataset_tools.convert import unpack_if_archive
import src.settings as s
from urllib.parse import unquote, urlparse
from supervisely.io.fs import get_file_name, get_file_size
import shutil
import json
from glob import glob

from tqdm import tqdm

def download_dataset(teamfiles_dir: str) -> str:
    """Use it for large datasets to convert them on the instance"""
    api = sly.Api.from_env()
    team_id = sly.env.team_id()
    storage_dir = sly.app.get_data_dir()

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, str):
        parsed_url = urlparse(s.DOWNLOAD_ORIGINAL_URL)
        file_name_with_ext = os.path.basename(parsed_url.path)
        file_name_with_ext = unquote(file_name_with_ext)

        sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
        local_path = os.path.join(storage_dir, file_name_with_ext)
        teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

        fsize = api.file.get_directory_size(team_id, teamfiles_dir)
        with tqdm(
            desc=f"Downloading '{file_name_with_ext}' to buffer...",
            total=fsize,
            unit="B",
            unit_scale=True,
        ) as pbar:        
            api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)
        dataset_path = unpack_if_archive(local_path)

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, dict):
        for file_name_with_ext, url in s.DOWNLOAD_ORIGINAL_URL.items():
            local_path = os.path.join(storage_dir, file_name_with_ext)
            teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

            if not os.path.exists(get_file_name(local_path)):
                fsize = api.file.get_directory_size(team_id, teamfiles_dir)
                with tqdm(
                    desc=f"Downloading '{file_name_with_ext}' to buffer...",
                    total=fsize,
                    unit="B",
                    unit_scale=True,
                ) as pbar:
                    api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)

                sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
                unpack_if_archive(local_path)
            else:
                sly.logger.info(
                    f"Archive '{file_name_with_ext}' was already unpacked to '{os.path.join(storage_dir, get_file_name(file_name_with_ext))}'. Skipping..."
                )

        dataset_path = storage_dir
    return dataset_path
    
def count_files(path, extension):
    count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                count += 1
    return count

def create_ann(image_path):
    filename = sly.fs.get_file_name_with_ext(image_path)
    labels = []

    height, width, tag_value = img_info_dict.get(filename)
    if filename in ann_dict:
        for bbox in ann_dict.get(filename):
            class_id = bbox[1]
            obj_class = classes_dict.get(int(class_id))
            xc, yc, w, h = bbox[0]
            xmin = xc - (w * 0.5)
            ymin = yc - (h * 0.5)
            xmax = xmin + w
            ymax = ymin + h
            rectangle = sly.Rectangle(ymin, xmin, ymax, xmax)
            label = sly.Label(rectangle, obj_class)
            labels.append(label)

    img_tag = sly.Tag(tm_dc, tag_value)

    return sly.Annotation(img_size=(height, width), labels=labels, img_tags=[img_tag])
tm_dc = sly.TagMeta("date captured", value_type=sly.TagValueType.ANY_STRING)

dataset_path = "/mnt/c/users/german/documents/hit-uav/normal_json"
ann_path = dataset_path + "/annotations"

id_filename_dict = {}
img_info_dict = {}
ann_id_dict = {}

anns_paths = sly.fs.list_files(ann_path)
for ann_file in anns_paths:
    f = open(ann_file)
    data = json.load(f)
    for path in data["images"]:
        id_filename_dict[path["id"]] = path["filename"]
        img_info_dict[path["filename"]] = path["height"], path["width"], path["date_captured"]
    for ann_path in data["annotation"]:
        if ann_path["image_id"] not in ann_id_dict:
            ann_id_dict[ann_path["image_id"]] = []
        ann_id_dict[ann_path["image_id"]].append((ann_path["bbox"], ann_path["category_id"]))
        
ann_dict = {id_filename_dict.get(k): v for k, v in ann_id_dict.items()}

classes_dict = {0: sly.ObjClass(name="person", geometry_type= sly.Rectangle,color=[0, 0, 255]),
1: sly.ObjClass(name="car", geometry_type= sly.Rectangle,color=[255, 0, 255]),
2: sly.ObjClass(name="bicycle", geometry_type= sly.Rectangle,color=[255, 0, 0]),
3: sly.ObjClass(name="other vehicle", geometry_type= sly.Rectangle,color=[0, 255, 0]),
4: sly.ObjClass(name="dontcare", geometry_type= sly.Rectangle,color=[0, 255, 255]),}


def convert_and_upload_supervisely_project(
    api: sly.Api, workspace_id: int, project_name: str
) -> sly.ProjectInfo:
    project = api.project.create(workspace_id, project_name)
    meta = sly.ProjectMeta(obj_classes=list(classes_dict.values()), tag_metas=[tm_dc])
    api.project.update_meta(project.id, meta.to_json())

    dir_paths = ["test", "train", "val"]

    batch_size = 50
    for ds in dir_paths:
        dspath = os.path.join(dataset_path, ds)
        dataset = api.dataset.create(project.id, ds, change_name_if_conflict=True)
        images_pathes = glob(os.path.join(dspath, "*"))
        progress = sly.Progress("Create dataset {}".format(ds), len(images_pathes))
        for img_pathes_batch in sly.batched(images_pathes, batch_size=batch_size):
            img_names_batch = [
                sly.fs.get_file_name_with_ext(im_path) for im_path in img_pathes_batch
            ]
            img_infos = api.image.upload_paths(dataset.id, img_names_batch, img_pathes_batch)
            img_ids = [im_info.id for im_info in img_infos]
            anns = [create_ann(image_path) for image_path in img_pathes_batch]
            api.annotation.upload_anns(img_ids, anns)
    return project


