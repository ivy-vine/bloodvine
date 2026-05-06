from wand.image import Image
import argparse
import os

def generate_icon(image_path, textures_path, team, threshold, out_path):
    # initialize some variables
    final_img_size = 591
    shrink_percent = 60

    # load image
    with Image(filename=image_path, format="png", background="transparent") as img:
        # first, extent (instead of resize to avoid stretching) to make the image a 1:1 aspect ratio
        # then, resize the image to the size it needs to be on the token
        # finally, extent to final_img_size
        size = max(img.width, img.height)
        img.extent(width=size, height=size, gravity="center")

        s = round(final_img_size * (shrink_percent / 100))
        img.resize(width=s, height=s)

        img.extent(width=final_img_size, height=final_img_size, gravity="center")

        # threshold the image to make it black and white
        img.colorspace = "gray"
        img.threshold(threshold=threshold, channel="gray")
        img.colorspace = "srgb"
        img.threshold(threshold=0.1, channel="alpha") # remove opacity

        with img.clone() as white:
            white.alpha_channel = "extract"
            white.transparent_color(color="black", alpha=0.0)

            with white.clone() as outline:
                outline.morphology(method="edge", kernel="octagon:3")

                with Image(filename=f"{textures_path}/parchment_back.png") as parchment_back:
                    outline.composite(image=parchment_back, operator="in")

                with Image(filename=f"{textures_path}/parchment.png") as parchment_noise:
                    parchment_noise.resize(width=final_img_size, height=final_img_size)
                    white.composite(image=parchment_noise, operator="in")
                
                outline.composite(white)

                with img.clone() as black:
                    black.transparent_color(color="white", alpha=0.0)
                    black.morphology(method="open", kernel="octagon:1")

                    with Image(filename=f"{textures_path}/{team}.png") as team_noise:
                        team_noise.resize(width=final_img_size, height=final_img_size)
                        black.composite(image=team_noise, operator="in")

                    with outline.clone() as result:
                        result.composite(black)

                        with result.clone() as shadow:
                            shadow.background_color = "black"
                            sig = 5
                            shadow.shadow(alpha=30, sigma=sig, x=0, y=0)

                            # we need to do this to composite because shadow makes the image bigger
                            with Image(width=img.width, height=img.height, background="transparent") as sized:
                                sized.composite(shadow, left=-(sig * 2))
                                sized.composite(result)

                                sized.save(filename=out_path)

parser = argparse.ArgumentParser(prog="generate icon", description="generate token icons for botc")
parser.add_argument("filepath")
parser.add_argument("team", choices=["good", "evil", "fabled", "loric", "traveller", "good_traveller", "evil_traveller", "minion", "outsider", "purple", "black"])
parser.add_argument("-t", "--threshold", type=float, default=0.5, help="threshold for turning the image mono. default=0.5")
parser.add_argument("-o", "--output", help="output location")
args = parser.parse_args()

if args.output:
    out_path = args.output
else:
    p1, p2 = os.path.split(args.filepath)
    out_path = os.path.join(
        os.path.split(args.filepath)[0],
        f"{os.path.splitext(p2)[0]}_{args.team}.png"
    )

generate_icon(args.filepath, "resources/textures", args.team, args.threshold, out_path)