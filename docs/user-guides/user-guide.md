# ChromaSense user guide

**Who this is for:** people with protan or deutan color vision deficiency who use ChromaSense in a web browser. It explains each step of the workflow, what each message means, and how your pictures are handled. No technical knowledge is needed.

ChromaSense helps people with red–green color vision deficiency tell apart colors in their own pictures. You upload a picture, choose your profile, and get a version where colors that are hard to tell apart are made lighter or darker. You can compare it with the original and download it.

It works the same way for photos, charts, maps, and other pictures. Results depend on the picture.

ChromaSense adjusts colors to help tell them apart. It does not diagnose color vision deficiency or give medical advice, and it does not show exactly what typical color vision sees.

## Open ChromaSense

On the computer that runs ChromaSense, open `http://localhost:9090` in Chrome, Edge, Firefox, or Safari.

From another computer or a phone on the same network:

1. On the computer that runs ChromaSense, find its network address:
   - **macOS:** `ipconfig getifaddr en0`
   - **Linux:** `hostname -I`
   - **Windows:** `ipconfig`, then find the IPv4 address of the active adapter
2. On the other device, open `http://<that address>:9090`, for example `http://192.168.1.20:9090`.

If the page does not open, the computer's firewall may be blocking port 9090. ChromaSense has no sign-in and is meant for your local network only.

## Step 1: Upload a picture

Choose **Choose a PNG or JPEG image** and pick a file. The picture uploads as soon as you choose it.

- Use a PNG or JPEG file, up to 10 MB and 12 megapixels. A typical phone photo fits.
- When the upload finishes, the original picture appears with its size.

## Step 2: Choose a profile and severity

1. Under **Color vision profile**, choose **Protan** or **Deutan**.
2. Set **Severity** from 0 to 1. It starts at 1. At 0, no adjustment is made for the profile; at 1, the full profile is used.
3. Choose **Enhance image**.

A message starting with **Enhancing:** appears, then one starting with **Done:** that says what ChromaSense found. If colors were adjusted, the comparison appears.

The button becomes available once you have uploaded a picture and chosen a profile. You can change the profile or severity and choose **Enhance image** again at any time.

## Step 3: Compare and download

When ChromaSense has adjusted colors, the comparison shows the enhanced picture on top of the original. Move the **Comparison position** slider to choose how far the enhanced picture covers the original from the left. At 50, the left half is enhanced and the right half is the original, so you can see the same area in both versions. With a keyboard, use the arrow keys on the slider.

Choose **Download enhanced PNG**, just below the message, to save the enhanced picture as `chromasense-enhanced.png`, at the same size as your original. This link appears only when ChromaSense has adjusted colors.

## What the messages mean

Messages appear below the upload control, and screen readers announce them. Each starts with a word that tells you its kind:

| Message starts with | Meaning |
| --- | --- |
| **Uploading:** | Your picture is being sent. |
| **Enhancing:** | ChromaSense is adjusting the colors. |
| **Done:** | The step finished. The rest of the message says what happened. |
| **Error:** | Something went wrong. The rest of the message says why. |

Messages you may see:

| Message | What to do |
| --- | --- |
| Adjusted 2 of 3 color pairs likely to be confused. | Compare and download the result. If some pairs could not be improved, the message says how many. |
| No colors likely to be confused were found for the deutan profile at severity 1. The original image is unchanged. | There is nothing to adjust for this profile. Try the other profile or a different severity. |
| Colors likely to be confused were found, but the adjustment could not increase their separation. The original image is still available. | ChromaSense could not help with this picture. |
| This file is not a PNG or JPEG image. | Save or export the picture as PNG or JPEG and try again. |
| This image file is damaged or incomplete and cannot be opened. | Try saving the picture again. |
| This file is larger than 10 MB. | Use a smaller file, for example by saving it as a JPEG. |
| This image is larger than 12 megapixels. | Resize the picture to 12 megapixels or less, for example 4000 by 3000 pixels. |

## Your pictures

You do not need an account. Your pictures are stored on the computer that runs ChromaSense only while you use the page. They are deleted when you close or reload the page, after 30 minutes without use, or when ChromaSense restarts.

## Keyboard and screen readers

Every step works with a keyboard. Press Tab to move between controls, the arrow keys to choose a profile or move a slider, and Enter or Space to choose a button or link. The first Tab stop is **Skip to main content**. The page also works at phone widths and with browser zoom.
