import os.path
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from PIL import Image
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
from dotenv import load_dotenv

load_dotenv("/Users/ayan/PycharmProjects/Image_Color_Processing/environ.env")


WORKING_WIDTH = 600
UPLOAD_FOLDER = "static/img/uploads"
EXTENSIONS = {'jpg', 'jpeg'}
img_path = ""

# ----------------------------- FLASK FRAMEWORK --------------------------- #

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = os.environ["API_KEY"]
Bootstrap5(app)


# ----------------------------- DEFINE FUNCTIONS --------------------------- #

def allowed_images(filename):
    """Checks if the uploaded image is of type .jpg or .jpeg"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSIONS


def process_colors(amount):
    """opens the Image with Pillow library, resizes it for faster processing time. Turns Image data into a NumPy
    3D-array (pixels in RGB color), reshapes it into 2D-array for processing. Groups similar arrays/colors with the
    help of KMeans clusters, amount set by User. Turns clustered 2D-array into list and converts single values into
    Integer for easier reuse of RGB colors. Returns list of RGB-colors."""
    global img_path
    img = Image.open(img_path)
    og_width = img.size[0]
    og_height = img.size[1]
    # resize image to lower processing times
    width_percentage = WORKING_WIDTH / og_width
    new_height = int(og_height * width_percentage)
    img = img.resize((WORKING_WIDTH, new_height))
    # convert image to NumPy arrays
    img_data = np.asarray(img)
    # reshape 3D array to 2D array
    # -1 means unknown number of rows, 3 means there's 3 columns (RGB)
    img_data = img_data.reshape(-1, 3)
    # use KMeans to cluster similar colors together
    color_cluster = KMeans(n_clusters=amount)
    color_cluster.fit(img_data)
    colors = color_cluster.cluster_centers_.tolist()
    # change float to int, for better UX with RGB colors
    color_palette = []
    for rgb_list in colors:
        new_colors = [int(value) for value in rgb_list]
        color_palette.append(new_colors)
    return color_palette


# ----------------------------- ROUTES --------------------------- #


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """renders 'index.html', if a file is chosen, uploads file to static/img/upload-directory, returns image-path,
        redirects to 'show-image.html'"""
    global img_path
    if request.method == "POST":
        image_file = request.files["file"]
        # If user does not select a file, the browser submits an empty file

        if image_file.filename == "":
            flash("Please select a file")
            return render_template("upload.html")

        if not allowed_images(image_file.filename):
            flash('The image has to be a ".jpg" or ".jpeg" file')
            return render_template("upload.html")
        if image_file and allowed_images(image_file.filename):
            # use secure_filename to prevent saving fraud files to the os
            filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            img_path = f"static/img/uploads/{filename}"
            return redirect(url_for("show_image")), img_path
    else:
        return render_template("upload.html")


@app.route("/show_image", methods=['GET', 'POST'])
def show_image():
    """renders 'show-image.html', shows image, gives Select Field for User Input, if select is used, calls
        function 'process_colors' with User Input as Input, renders the Output as RGB color palette"""
    global img_path
    if request.method == "POST":
        amount_of_colors = int(request.form.get("amount"))
        top_colors = process_colors(amount_of_colors)
        colors = []
        for color in top_colors:
            colors.append(tuple(color))
        return render_template("show_image.html", image_path=img_path, colors=colors, palette=True)
    else:
        return render_template("show_image.html", image_path=img_path, palette=False)


if __name__ == "__main__":
    app.run(debug=True)
