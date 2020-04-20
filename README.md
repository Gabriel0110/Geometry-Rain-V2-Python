# Geometry-Rain-V2-Python
I recreated my Geometry Rain game in Python that I initially made with Unity in C#.  The main reason for this is to more easily train Reinforcement Learning agents using various algorithms to play the game and see how well they learn to play it.  I'll likely use OpenAI Gym to create my own environment of the game.

I haven't separated the classes into their own files yet, so you can simply install the necessary library (Arcade) and run the geometry_rain.py file.

You can check out the gif below of a demo video, showcasing the basics.

The idea:
- Avoid red circles -- you will lose if they hit you
- Get yellow squares -- they give bonus points, and if you get 5 in a row without letting one hit the bottom of the screen or without getting hit by a trap, you can activate a bonus ability that slows down the enemy spawn rate for a few seconds, giving you some breathing time.
- Avoid green trapezoids -- you will lose points and any bonus streak you had, and they slow you quite a lot, causing you to have a more difficulty time dodging the red circles.
- Take a chance -- collect the rainbow stars that randomly spawn, and you will get a random power-up.. or power-down, who knows!
- Every 4 levels is a hard-mode level.  The speed of red circles dropping is incredibly fast -- watch out!
- See how long you can survive and rack up points.  Points are given every second you are alive.  Combine your survival time with bonus shapes (yellow squares), and see how many points you can get.

![](geometry_rain_demo_gif.gif)
