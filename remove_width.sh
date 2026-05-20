#!/bin/bash
files=("blog.html" "road-trip.html" "satellite-events.html" "side-events.html" "adopting-bitcoin-cape-town-brand.html" "bce-summit.html" "bitcoinloxion-round-trips.html" "experience-victoria-falls.html" "404.html")
for file in "${files[@]}"; do
  sed -i "s/ width=\"Auto\"//g" "$file"
done
echo "All width=\"Auto\" instances removed successfully"
