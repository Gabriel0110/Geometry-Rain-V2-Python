import arcade
import random
import time
import pyautogui
import pickle
from arcade.gui import *

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = round(pyautogui.size()[1]*0.8)
#SCREEN_HEIGHT = 1200
SCREEN_TITLE = "Geometry Rain"
#SCALING = 1.0
app = None
game = None

def getButtonThemes():
    theme = Theme()
    theme.set_font(24, arcade.color.BLACK)
    normal = "images/Normal.png"
    hover = "images/Hover.png"
    clicked = "images/Clicked.png"
    locked = "images/Locked.png"
    theme.add_button_textures(normal, hover, clicked, locked)
    return theme

class PlayButton(TextButton):
    def __init__(self, view, x=0, y=0, width=100, height=40, text="Play", theme=None):
        super().__init__(x, y, width, height, text, theme=theme)
        self.view = view
        self.text = text

    def on_press(self):
        global game, app
        app = GeometryRain()
        game.show_view(app)
        app.setup()

class ExitButton(TextButton):
    def __init__(self, view, x=0, y=0, width=100, height=40, text="Exit", theme=None):
        super().__init__(x, y, width, height, text, theme=theme)

    def on_press(self):
        #self.pressed = True
        exit()

class MainMenu(arcade.View):
    def __init__(self):
        super().__init__()

        self.theme = getButtonThemes()
        self.button_list.append(PlayButton(self, SCREEN_WIDTH*0.25, SCREEN_HEIGHT*0.25, 110, 50, theme=self.theme))
        self.button_list.append(ExitButton(self, SCREEN_WIDTH*0.75, SCREEN_HEIGHT*0.25, 110, 50, theme=self.theme))

        self.background = arcade.load_texture("images/title_screen.jpg")

    def on_show(self):
        arcade.set_background_color(arcade.color.GRAY)

    def on_draw(self):
        arcade.start_render()
        scale = SCREEN_WIDTH / self.background.width
        arcade.draw_lrwh_rectangle_textured(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, self.background)
        arcade.draw_text("GEOMETRY RAIN", SCREEN_WIDTH/2, SCREEN_HEIGHT*0.7, arcade.color.WHITE, font_size=60, font_name='GOTHIC', anchor_x="center", bold=True)
        for button in self.button_list:
            button.draw()

class GeometryRain(arcade.View):
    def __init__(self):
        """Initialize the game
        """
        super().__init__()

        self.height = SCREEN_HEIGHT
        self.width = SCREEN_WIDTH

        # Set up the empty sprite lists
        self.enemies_list = arcade.SpriteList()
        self.bonuses_list = arcade.SpriteList()
        self.traps_list = arcade.SpriteList()
        self.mysteries_list = arcade.SpriteList()
        self.bullets_list = arcade.SpriteList()
        self.all_sprites = arcade.SpriteList()

        self.paused = False

        # Init score for scoreboard
        self.score = 0
        self.highscore = 0
        self.bonus_count = 0
        self.level = 1
        self.level_timer = 45

        self.BONUS_AVAILABLE = False
        self.BONUS_ACTIVE = False
        self.bonus_start_time = 0
        self.bonus_text = ""

        self.enemy_spawn_time = 0.5
        self.bonus_spawn_time = 8.0
        self.trap_spawn_time = 3.0
        self.point_increase_time = 0.5
        self.level_increase_time = 45

        self.enemy_collision_radius = 0.0

        self.TRAP_HIT = False

        # Velocities so you can edit them
        self.enemy_pre_change_velocity = 0
        self.enemy_velocity = (0, random.randint(-7, -3))
        self.player_velocity = 15
        self.bonus_velocity_change = (0, -2)
        
        self.HARDMODE_ACTIVE = False
        self.hardmode_start_time = 0
        self.hardmode_duration = 13

        self.score_text = None
        self.bonus_streak_text = None
        self.level_text = None
        self.next_level_text = None
        self.godmode_active_text = None

        # Mystery Sprite variables
        self.mystery_effect_start_time = 0
        self.MYSTERY_EFFECT_ACTIVE = False
        self.effect = 0
        self.balloon_on = False
        self.mystery_text = ""
        self.follow_effect_active = False

        # FOR TESTING - set to "True" to not lose when hit by enemy.  Otherwise, KEEP "False"
        self.GOD_MODE = False

    def setup(self):
        """Get the game ready to play
        """
        # See if there is a previous score to load for high score
        try:
            with open('saved_score.dat', 'rb') as file:
                self.highscore = pickle.load(file)
        except Exception as e:
            print(f"Error attempting to load saved highscore: {e}")
            print("Setting highscore to 0.")
            self.highscore = 0

        # Set the background color
        arcade.set_background_color(arcade.color.SKY_BLUE)

        # Set up the player
        self.player = arcade.Sprite("images/player_sprite.png", 0.20)
        self.player.center_y = 40
        self.player.left = self.width / 2
        self.all_sprites.append(self.player)

        # Spawn a new enemy every 0.5 seconds
        arcade.schedule(self.add_enemy, self.enemy_spawn_time)

        # Spawn a new bonus every 8 seconds
        arcade.schedule(self.add_bonus, self.bonus_spawn_time)

        # Spawn a trap every 5 seconds
        arcade.schedule(self.add_trap, self.trap_spawn_time)

        # Check if mystery sprite can be spawned
        arcade.schedule(self.add_mystery, 20.0)

        # Give points every half a second the player is alive
        arcade.schedule(self.givePoints, self.point_increase_time)

        # Increase level and difficulty every 45 seconds
        #arcade.schedule(self.increaseLevel, self.level_increase_time)

        # Edit time counter for next level
        arcade.schedule(self.countdown, 1.0)

    def on_update(self, delta_time: float):
        global app, game
        """Update the positions and statuses of all game objects
        If paused, do nothing

        Arguments:
            delta_time {float} -- Time since the last update
        """

        # If paused, don't update anything
        if self.paused:
            return

        # Did you hit an enemy?
        if self.player.collides_with_list(self.enemies_list):
            if not self.GOD_MODE:
                # Save the highscore and end the game
                if self.score >= self.highscore:
                    with open('saved_score.dat', 'wb') as file:
                        pickle.dump(self.score, file)
                game.show_view(MainMenu())

        # Check if bonus streak if 5 to award bonus ability
        if self.bonus_count == 5:
            # GIVE ABILITY POPUP and clear streak count, and start timer for duration
            self.BONUS_AVAILABLE = True
            self.bonus_text = "BONUS READY - PRESS 'Spacebar'"
        
        # Check if duration ran out and end bonus if so, resetting values
        if self.BONUS_ACTIVE:
            if (time.time() - self.bonus_start_time) >= 10:
                print("Bonus ran out of time -- ending bonus ability.")
                self.BONUS_ACTIVE = False
                self.bonus_start_time = 0
                self.enemy_spawn_time -= 0.5
                arcade.unschedule(self.add_enemy)
                arcade.schedule(self.add_enemy, self.enemy_spawn_time)
                self.enemy_velocity = self.enemy_pre_change_velocity
                for enemy in self.enemies_list:
                    enemy.velocity = self.enemy_pre_change_velocity

        if self.follow_effect_active == True:
            self.followEffect()

        # Check if mystery duration ran out
        if self.MYSTERY_EFFECT_ACTIVE:
            if self.follow_effect_active:
                if (time.time() - self.mystery_effect_start_time) >= 7:
                    self.removeEffect()
            else:
                if (time.time() - self.mystery_effect_start_time) >= 10:
                    self.removeEffect()

        # Update everything
        self.all_sprites.update()

        # Keep the player on screen
        if self.player.top > self.height:
            self.player.top = self.height
        if self.player.right > self.width:
            self.player.right = self.width
        if self.player.bottom < 0:
            self.player.bottom = 0
        if self.player.left < 0:
            self.player.left = 0

    def on_draw(self):
        """Draw all game objects
        """
        # Begin rendering (will end automatically after method ends)
        arcade.start_render()

        # Draw scoreboard text
        if not self.HARDMODE_ACTIVE:
            self.highscore_text = arcade.draw_text("HIGH SCORE: {}".format(str(self.highscore)), self.width/2 - 75, self.height - 35, arcade.color.BLACK, 18)
            self.score_text = arcade.draw_text("SCORE: {}".format(str(self.score)), self.width/2 - 75, self.height - 65, arcade.color.BLACK, 18)
            self.bonus_streak_text = arcade.draw_text("Bonus Streak: {}/5".format(str(self.bonus_count)), self.width/2 - 75, self.height - 95, arcade.color.BLACK, 18)
            self.level_text = arcade.draw_text("Level: {}".format(str(self.level)), self.width - 175, self.height - 35, arcade.color.BLACK, 18)
            self.next_level_text = arcade.draw_text("Next level in: {}".format(str(self.level_timer)), self.width - 175, self.height - 65, arcade.color.BLACK, 18)
        else:
            arcade.set_background_color(arcade.color.BLACK)
            self.highscore_text = arcade.draw_text("HIGH SCORE: {}".format(str(self.highscore)), self.width/2 - 75, self.height - 35, arcade.color.WHITE, 18)
            self.score_text = arcade.draw_text("SCORE: {}".format(str(self.score)), self.width/2 - 75, self.height - 65, arcade.color.WHITE, 18)
            self.bonus_streak_text = arcade.draw_text("Bonus Streak: {}/5".format(str(self.bonus_count)), self.width/2 - 75, self.height - 95, arcade.color.WHITE, 18)
            self.level_text = arcade.draw_text("Level: {}".format(str(self.level)), self.width - 175, self.height - 35, arcade.color.WHITE, 18)
            self.next_level_text = arcade.draw_text("Next level in: {}".format(str(self.level_timer)), self.width - 175, self.height - 65, arcade.color.WHITE, 18)

        # Sanity check to let you know that god mode is active when using it
        if self.GOD_MODE:
            if self.HARDMODE_ACTIVE:
                self.godmode_active_text = arcade.draw_text("GOD MODE ACTIVE", self.width*0.02, self.height - 35, arcade.color.WHITE, 18)
            else:
                self.godmode_active_text = arcade.draw_text("GOD MODE ACTIVE", self.width*0.02, self.height - 35, arcade.color.BLACK, 18)
        
        # Draw placeholder text for bonus notification
        if self.BONUS_AVAILABLE:
            arcade.draw_text(self.bonus_text, self.width/2 - 75, self.height*0.05, arcade.color.BLACK, 18)

        if self.MYSTERY_EFFECT_ACTIVE:
            color = arcade.color.BLACK if not self.HARDMODE_ACTIVE else arcade.color.WHITE
            if self.effect == 1:
                # Small player
                arcade.draw_text(self.mystery_text, self.width/2 - 75, self.height/2 + 50, color, 18)
            elif self.effect == 2:
                # Ballooning
                arcade.draw_text(self.mystery_text, self.width/2 - 75, self.height/2 + 50, color, 18)
            elif self.effect == 3:
                # Enemies shoot
                arcade.draw_text(self.mystery_text, self.width/2 - 75, self.height/2 + 50, color, 18)
            elif self.effect == 4:
                # Enemies follow
                arcade.draw_text(self.mystery_text, self.width/2 - 75, self.height/2 + 50, color, 18)
            elif self.effect == 5:
                pass
            elif self.effect == 6:
                pass

        self.all_sprites.draw()

    def on_key_press(self, key, modifiers):
        """Handle user keyboard input
        Q: Quit the game
        P: Pause/Unpause the game
        I/J/K/L: Move Up, Left, Down, Right
        Arrows: Move Up, Left, Down, Right

        Arguments:
            symbol {int} -- Which key was pressed
            modifiers {int} -- Which modifiers were pressed
        """
        if key == arcade.key.Q:
            # Quit immediately
            arcade.close_window()

        if key == arcade.key.P:
            self.paused = not self.paused

        if key == arcade.key.SPACE:
            if self.BONUS_AVAILABLE:
                if not self.HARDMODE_ACTIVE: # can't use bonus in hardmode ;)
                    self.bonus_text = ""
                    self.BONUS_ACTIVE = True
                    self.BONUS_AVAILABLE = False
                    self.bonus_count = 0
                    self.bonus_start_time = time.time()

                    # Ability effect
                    self.enemy_spawn_time += 0.5
                    arcade.unschedule(self.add_enemy)
                    arcade.schedule(self.add_enemy, self.enemy_spawn_time)
                    self.enemy_pre_change_velocity = self.enemy_velocity
                    self.enemy_velocity = self.bonus_velocity_change
                    for enemy in self.enemies_list:
                        enemy.velocity = self.bonus_velocity_change

        if key == arcade.key.A or key == arcade.key.LEFT:
            self.player.change_x = -self.player_velocity
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.player.change_x = self.player_velocity
        elif (key == arcade.key.W or key == arcade.key.UP) and self.follow_effect_active:
            self.player.change_y = self.player_velocity
        elif (key == arcade.key.S or key == arcade.key.DOWN) and self.follow_effect_active:
            self.player.change_y = -self.player_velocity

    def on_key_release(self, key: int, modifiers: int):
        """Undo movement vectors when movement keys are released

        Arguments:
            symbol {int} -- Which key was pressed
            modifiers {int} -- Which modifiers were pressed
        """
        if (
            key == arcade.key.W
            or key == arcade.key.S
            or key == arcade.key.UP
            or key == arcade.key.DOWN
        ):
            self.player.change_y = 0

        if (
            key == arcade.key.A
            or key == arcade.key.D
            or key == arcade.key.LEFT
            or key == arcade.key.RIGHT
        ):
            self.player.change_x = 0

    def countdown(self, delta_time: float):
        if not self.paused:
            self.level_timer -= 1
            if self.level_timer < 0 and self.HARDMODE_ACTIVE == True:
                self.HARDMODE_ACTIVE = False
                arcade.set_background_color(arcade.color.SKY_BLUE)
                self.enemy_spawn_time = 0.5
                arcade.unschedule(self.add_enemy)
                arcade.schedule(self.add_enemy, self.enemy_spawn_time)
                self.hardmode_start_time = 0
                try:
                    self.increaseLevel()
                except Exception as e:
                    print(f"ERROR: {e}")
                # enemy_velocity will be set back to normal automatically -- see velocity in add_enemy(), it checks for hardmode
            elif self.level_timer < 0 and self.HARDMODE_ACTIVE == False:
                try:
                    self.increaseLevel()
                except Exception as e:
                    print(f"ERROR: {e}")
        else:
            return

    def givePoints(self, delta_time: float):
        if self.paused:
            return
        else:
            self.score += 50
            if self.score > self.highscore:
                self.highscore = self.score

    def increaseLevel(self):
        self.level += 1

        # HARD MODE
        if self.level % 4 == 0 and self.HARDMODE_ACTIVE == False:
            # Stop all spawning for 5 seconds, give it some suspense, change background color to black, then start hard mode dropping
            self.hardMode()
        else:
            self.level_timer = 45

        # Increase enemy movement speed slightly if not in hardmode
        if self.HARDMODE_ACTIVE == False:
            new_velocity = (0, list(self.enemy_velocity)[1] - 0.7)
            self.enemy_pre_change_velocity = new_velocity
            self.enemy_velocity = new_velocity

    def hardMode(self):
        self.MYSTERY_EFFECT_ACTIVE = False
        self.removeEffect()
        self.HARDMODE_ACTIVE = True

        arcade.set_background_color(arcade.color.BLACK)

        # Change level timer
        self.level_timer = self.hardmode_duration

        self.hardmode_start_time = time.time()

        # Increase spawn rate
        self.enemy_spawn_time = 0.05
        arcade.unschedule(self.add_enemy)
        arcade.schedule(self.add_enemy, self.enemy_spawn_time)

        # Now that HARDMODE_ACTIVE is true, in add_enemy(), the spawn rate will change until set to False

    def add_enemy(self, delta_time: float):
        """Adds a new enemy to the screen

        Arguments:
            delta_time {float} -- How much time has passed since the last call
        """
        if self.paused:
            return

        # Check if hardmode is on and how long it has been on for
        if self.HARDMODE_ACTIVE:
            # If hardmode has been on for less than 5 seconds, don't spawn anything.
            if (time.time() - self.hardmode_start_time) < 5:
                return

        if not self.BONUS_ACTIVE:
            if not self.HARDMODE_ACTIVE:
                # Everything is normal play - set velocity to new random
                self.enemy_velocity = (0, random.randint(-7, -3))

        # First, create the new enemy sprite
        enemy = EnemySprite("images/enemy_sprite.png", 0.15)

        # Set its position to a random x position and off-screen at the top
        enemy.top = random.randint(self.height, self.height + 80)
        enemy.left = random.randint(10, self.width - 10)

        # Set its speed to a random speed heading down
        if self.HARDMODE_ACTIVE:
            enemy.velocity = (0, random.randint(-18, -15))
        else:
            enemy.velocity = self.enemy_velocity

        # Add it to the enemies list and all_sprites list
        self.enemies_list.append(enemy)
        self.all_sprites.append(enemy)

    def add_bonus(self, delta_time: float):
        if self.paused:
            return

        if self.BONUS_ACTIVE:
            return

        if self.HARDMODE_ACTIVE:
            return

        bonus = BonusSprite("images/bonus_sprite.png", 0.3)

        # Set its position to a random x position and off-screen at the top
        bonus.top = random.randint(self.height, self.height + 80)
        bonus.left = random.randint(10, self.width - 10)

        # Set its speed to a random speed heading down
        bonus.velocity = (0, -3) # x doesn't do anything, but y decreases by amount

        # Add it to the enemies list and all_sprites list
        self.bonuses_list.append(bonus)
        self.all_sprites.append(bonus)

    def add_trap(self, delta_time: float):
        if self.paused:
            return

        trap = TrapSprite("images/trap_sprite.png", 0.3)

        # Set its position to a random x position and off-screen at the top
        trap.top = random.randint(self.height, self.height + 80)
        trap.left = random.randint(10, self.width - 10)

        # Set its speed to a random speed heading down
        trap.velocity = (0, -5) # x doesn't do anything, but y decreases by amount

        # Add it to the enemies list and all_sprites list
        self.traps_list.append(trap)
        self.all_sprites.append(trap)

    def add_mystery(self, delta_time: float):
        if self.paused:
            return

        spawn_check = random.randint(0, 4)
        if spawn_check == random.randint(0, 4):
            if self.HARDMODE_ACTIVE == False:
                self.MYSTERY_EFFECT_ACTIVE = True
                self.effect = random.choice([1, 2, 3, 4, 5, 6])
                self.activateEffect()
        else:
            return # no spawn

    def add_bullet_for_enemy(self, enemy):
        if self.paused:
            return

        bullet = Bullet("images/enemy_sprite.png", 0.05)

        # Position the bullet
        bullet.center_y = enemy.center_y
        bullet.center_x = enemy.center_x

        # Give the bullet a speed
        bullet.velocity = (0, -8)

        # Add the bullet to the appropriate lists
        self.bullets_list.append(bullet)
        self.all_sprites.append(bullet)

    def activateEffect(self):
        #self.effect = 4
        if self.effect == 1:
            self.mystery_text = "SHRINK RAY"
            self.player._set_scale(0.1)
            self.player._set_collision_radius(self.player._get_collision_radius() / 2)
            self.mystery_effect_start_time = time.time() # last for 10 seconds then go back
        elif self.effect == 2:
            self.mystery_text = "MIND THE GAPS"
            arcade.schedule(self.balloonEffect, 1.0)
            self.mystery_effect_start_time = time.time()
        elif self.effect == 3:
            self.mystery_text = "MAKE IT RAIN"
            arcade.schedule(self.shootBulletsEffect, 1.0)
            self.mystery_effect_start_time = time.time()
        elif self.effect == 4:
            self.mystery_text = "RUN...\n(you can move up and down)"
            self.follow_effect_active = True
            self.mystery_effect_start_time = time.time()
        elif self.effect == 5:
            pass
        elif self.effect == 6:
            pass

    def removeEffect(self):
        if self.effect == 1:
            self.MYSTERY_EFFECT_ACTIVE = False
            self.player._set_scale(0.25)
            self.player._set_collision_radius(self.player._get_collision_radius() * 2)
            self.mystery_effect_start_time = 0
            self.effect = 0
        elif self.effect == 2:
            arcade.unschedule(self.balloonEffect)
            self.MYSTERY_EFFECT_ACTIVE = False
            for enemy in self.enemies_list:
                enemy._set_scale(0.15)
            self.mystery_effect_start_time = 0
            self.effect = 0
        elif self.effect == 3:
            arcade.unschedule(self.shootBulletsEffect)
            self.MYSTERY_EFFECT_ACTIVE = False
            self.mystery_effect_start_time = 0
            self.effect = 0
        elif self.effect == 4:
            self.follow_effect_active = False
            self.mystery_effect_start_time = 0
            self.effect = 0
            for sprite in self.enemies_list:
                sprite.remove_from_sprite_lists()
            self.player.left = self.width/2 - 75
            self.player.center_y = 40
        elif self.effect == 5:
            pass
        elif self.effect == 6:
            pass

    def balloonEffect(self, delta_time: float):
        if self.paused or not self.MYSTERY_EFFECT_ACTIVE:
            return

        if self.effect == 2:
            if not self.balloon_on:
                for enemy in self.enemies_list:
                    enemy._set_scale(0.6)
                    #enemy._set_collision_radius(app.enemy_collision_radius * 4)
                self.balloon_on = True
            else:
                for enemy in self.enemies_list:
                    enemy._set_scale(0.15)
                    #enemy._set_collision_radius(app.enemy_collision_radius)
                self.balloon_on = False

    def shootBulletsEffect(self, delta_time: float):
        if self.paused or not self.MYSTERY_EFFECT_ACTIVE:
            return
        if self.effect == 3:
            for enemy in self.enemies_list:
                self.add_bullet_for_enemy(enemy)

    def followEffect(self):
        for enemy in self.enemies_list:
            enemy.follow(self.player)
    

class EnemySprite(arcade.Sprite):
    def update(self):
        """Update the position of the sprite"""

        # Move the sprite
        super().update()

        # Remove if off the screen and increase score
        if self.bottom <= 5:
            self.remove_from_sprite_lists()
            #app.score += self.getPointValue()

    def follow(self, player):
        import math
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Random 50% chance that we'll change from our old direction and
        # then re-aim toward the player
        if random.randrange(1) == 0:
            start_x = self.center_x
            start_y = self.center_y

            # Get the destination location for the bullet
            dest_x = player.center_x
            dest_y = player.center_y

            # Do math to calculate how to get the bullet to the destination.
            # Calculation the angle in radians between the start points
            # and end points. This is the angle the bullet will travel.
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)

            # Taking into account the angle, calculate our change_x
            # and change_y. Velocity is how fast the bullet travels.
            self.velocity = (math.cos(angle) * 1.0, math.sin(angle) * 1.0)


class BonusSprite(arcade.Sprite):
    def update(self):
        super().update()

        if self.bottom <= 5:
            self.remove_from_sprite_lists()
            app.bonus_count = 0

        if self.collides_with_sprite(app.player):
            self.remove_from_sprite_lists()
            app.score += self.getPointValue()
            app.player_velocity = 15
            if not app.BONUS_AVAILABLE:
                app.bonus_count += 1
            
            if app.TRAP_HIT:
                app.TRAP_HIT = False
    
    def getPointValue(self):
        point_value = 500
        return point_value

class TrapSprite(arcade.Sprite):
    def update(self):
        super().update()

        if self.bottom <= 5:
            self.remove_from_sprite_lists()

        if self.collides_with_sprite(app.player):
            app.TRAP_HIT = True
            self.remove_from_sprite_lists()
            app.score += self.getPointValue()
            app.bonus_count = 0 # reset bonus streak
            app.player_velocity = 3
    
    def getPointValue(self):
        point_value = -500 # WILL LOSE 500
        return point_value

class Bullet(arcade.Sprite):
    def update(self):
        super().update()
        
        if self.bottom <= 5:
            self.remove_from_sprite_lists()

        if self.collides_with_sprite(app.player):
            self.remove_from_sprite_lists()
            app.score -= 50
            app.bonus_count = 0 # reset bonus streak
            app.player_velocity = 0.5

def start():
    global game
    game = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    main_menu = MainMenu()
    game.show_view(main_menu)
    arcade.run()

if __name__ == "__main__":
    start()
