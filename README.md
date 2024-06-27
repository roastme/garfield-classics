# garfield-classics
A script that tries to scrape [Garfield Classics](https://assets.amuniversal.com/c9e341a00fce0134687e005056a9545d) from `web.archive.org`, following their removal from `gocomics.com` on December 2, 2023.

After full completion (around 3-6 hours), the expected final size of the folder is around 250MB.

## Known Bugs
Comics before February 2017 are low-quality (600px wide). To help you distinguish between the two, the script saves low-resolution comics in a separate folder called `garfield_classics_low_res`. The user can delay their download by removing all the dates from 2016 in `garfield_dates.txt`. To obtain the full 900px wide version of these comics, you can use the zoom feature on the 2016 version of the site. Here's how to do it:

1. Navigate to the URL for the comic on web.archive.org.
2. Use the Wayback Machine to select a date when the comic was available.
3. Once the comic loads, use your browser's zoom feature to zoom in on the comic until it is 900px wide.
4. Save the image using your browser's 'Save Image As' feature.

This process can be time-consuming, but it will allow you to obtain higher-quality versions of the comics from before February 2017.
