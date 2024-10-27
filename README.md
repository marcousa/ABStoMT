# ABStoMT
 Audiobookshelf integration to MediaTracker using Socket.io events from ABS

# What is this?
ABStoMT is a Socket.io based connector between [Audiobookshelf](https://github.com/advplyr/audiobookshelf) and [MediaTracker](https://github.com/bonukai/MediaTracker)
It allows progress for audiobooks to be periodically updated automatically into MediaTracker as you're listening to an item from Audiobookshelf.
If the item you're listening to is not in your MediaTracker library yet, it will be added automatically.
<br>  
**The item in your Audiobookshelf library MUST have an ASIN number tied to it for the integration to work**

# Docker Compose

```yml
services:
  abstomt:
    container_name: ABStoMT
    image: cyberflip/abstomt
    restart: unless-stopped
    environment:
      TZ: "America/New_York"
      PUID: 1000 #modify based on your environment
      PGID: 1000 #modify based on your environment
      AUDIOBOOKSHELF_URL: "ENTER YOUR AUDIOBOOKSHELF INSTANCE URL HERE"
      AUDIOBOOKSHELF_USERNAME: "ENTER YOUR AUDIOBOOKSHELF ID HERE"
      AUDIOBOOKSHELF_PASSWORD: "ENTER YOUR AUDIOBOOKSHELF ID PASSWORD HERE"
      MEDIATRACKER_URL: "ENTER YOUR MEDIATRACKER INSTANCE URL HERE"
      MEDIATRACKER_TOKEN: "ENTER AN API TOKEN CREATED IN MEDIATRAKCER HERE"
```

The image is available on [DockerHub](https://hub.docker.com/r/cyberflip/abstomt)
