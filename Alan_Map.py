"""
Programming's project
"""
import arcade
import math

# Constants
# ======================================================================================================================

# Screen
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 650
SCREEN_TITLE = "Super JOANA"

# Size of our sprites
CHARACTER_SCALING = 1
TILE_SCALING = 0.5
COIN_SCALING = 0.5
SPRITE_LASER_SCALING = 0.8
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = (SPRITE_PIXEL_SIZE*TILE_SCALING)
SPRITE_SIZE = int(SPRITE_PIXEL_SIZE*TILE_SCALING)

# How many pixels to keep with each side of the camera
LEFT_VIEWPORT_MARGIN = 250
RIGHT_VIEWPORT_MARGIN = 250
BOTTOM_VIEWPORT_MARGIN = 250
TOP_VIEWPORT_MARGIN = 100

# Player
PLAYER_MOVEMENT_SPEED = 3 # horizontal speed
PLAYER_JUMP_SPEED = 13 # vertical speed
PLAYER_START_X = 250 # starting position (x coordinate)
PLAYER_START_Y = 2700 # starting position (y coordinate)
UPDATES_PER_FRAME = 4 # speed of the animation
RIGHT_FACING = 0 # looks to the right at the start
LEFT_FACING = 1 # looks to the left when walking to the left

# Other
GRAVITY = 0.8
BULLET_SPEED = 10
EXPLOSION_TEXTURE_COUNT = 60
# ======================================================================================================================

# Define texture to extract resources from th the arcade library
# ======================================================================================================================
def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True)
    ]
# ======================================================================================================================

# Create a class for the player
# ======================================================================================================================
class PlayerCharacter(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.character_face_direction = RIGHT_FACING # Will face right when = 0 and left when = 1

        # flipping between images
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Adjust the collision box (the four corners)
        self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]

        # Load the player's sprite
        main_path = ":resources:images/animated_characters/female_adventurer/femaleAdventurer"

        # load texture for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")

        # Walking
        self.walk_textures = []
        for i in range(8):
            # load all the frame to create the animation when walking
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

    def update_animation(self, delta_time: float = 1/60):

        # figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # idle animation
        if self.change_x == 0 and self.change_y == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Walking animation
        self.cur_texture += 1
        if self.cur_texture > 7 * UPDATES_PER_FRAME:
            self.cur_texture = 0
        frame = self.cur_texture // UPDATES_PER_FRAME
        direction = self.character_face_direction
        self.texture = self.walk_textures[frame][direction]
# ======================================================================================================================

#  Create a class for the explosion
# ======================================================================================================================
class Explosion(arcade.Sprite):

    def __init__(self, texture_list):
        # Start at the first frame
        super().__init__()
        self.current_texture = 0
        self.textures = texture_list

    def update(self):
        # Move to the next frame until the animation is over
        self.current_texture += 1
        if self.current_texture < len(self.textures):
            self.set_texture(self.current_texture)
        else:
            self.remove_from_sprite_lists()
# ======================================================================================================================

# Create a class for the game
# ======================================================================================================================
class MyGame(arcade.Window):
    """
    Main application class.
    """

    # Init
    # =================
    def __init__(self):
        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # These are 'lists' that keep track of our sprites
        self.coin_list = None
        self.wall_list = None
        self.player_list = None
        self.enemy_list = None
        self.bullet_list = None
        self.bullet_enemy_list = None
        self.explosion_list = None
        self.ladder_list = None
        self.background_list = None
        self.foreground_list = None
        self.dont_touch_list = None
        self.trampoline_list = None

        # Enemies that shoot me
        self.frame_count = 0

        # Remove the comment if you don't want to see the mouse cursor
        #self.set_mouse_visible(False)

        # Pre-load the animation frames.
        self.explosion_texture_list = []
        columns = 16
        count = 60
        sprite_width = 256
        sprite_height = 256
        file_name = f":resources:images/spritesheets/explosion.png"

        # Load the explosion from a sprite sheet
        self.explosion_texture_list = arcade.load_spritesheet(file_name, sprite_width, sprite_height, columns, count)

        # Keep track of the score and life
        self.score = 0
        self.life = 5

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our physics engine
        self.physics_engine = None

        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        # right edge of the map
        self.end_of_map = 0

        # Starting level when loading the game
        self.level = 5

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")
        self.game_over = arcade.load_sound(":resources:sounds/gameover1.wav")
        self.gun_sound = arcade.sound.load_sound(":resources:sounds/laser1.wav")
        self.hit_sound = arcade.sound.load_sound(":resources:sounds/explosion2.wav")

        # Put a blue background
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

        # Add timer
        self.total_time = 0.0
    # =======================

    # Setup the game
    # ====================
    def setup(self, level):
        """ Set up the game here. Call this function to restart the game. """

        # Used to keep track of our scrolling
        self.view_bottom = 0
        self.view_left = 0

        # Reset the initial value at beginning of every new level
        self.score = 0
        self.life = 5

        # Create the Sprite lists
        self.player_list = arcade.SpriteList()
        self.trampoline_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.foreground_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.explosion_list = arcade.SpriteList()
        self.bullet_enemy_list = arcade.SpriteList()
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.player_list.append(self.player_sprite)

        # Name of the layer from tiled
        platform_layer_name = "ground"
        coins_layer_name = "Coins" # items you can collect
        foreground_layer_name = "Foreground"
        background_layer_name = "Background"
        dont_touch_layer_name = "Don't touch" # will kill you if you touch them
        trampoline_layer_name = "Trampoline" # will make you jump higher
        enemy_layer_name = "Enemies"
        ladder_layer_name = "Ladder"

        # Map name
        map_name = f"map2_level_{self.level}.tmx"

        # read in the tiled map
        my_map = arcade.tilemap.read_tmx(str(map_name))

        # calculate the right edge of my_map
        self.end_of_map = my_map.map_size.width * GRID_PIXEL_SIZE

        # Link the layer from tiled with our game
        self.background_list = arcade.tilemap.process_layer(my_map, background_layer_name, TILE_SCALING)
        self.foreground_list = arcade.tilemap.process_layer(my_map, foreground_layer_name, TILE_SCALING)
        self.coin_list = arcade.tilemap.process_layer(my_map, coins_layer_name, TILE_SCALING, use_spatial_hash=True)
        self.dont_touch_list = arcade.tilemap.process_layer(my_map, dont_touch_layer_name, TILE_SCALING, use_spatial_hash=True)
        self.trampoline_list = arcade.tilemap.process_layer(my_map, trampoline_layer_name, TILE_SCALING, use_spatial_hash=True)
        self.enemy_list = arcade.tilemap.process_layer(my_map, enemy_layer_name, TILE_SCALING)
        self.ladder_list = arcade.tilemap.process_layer(my_map, ladder_layer_name, TILE_SCALING, use_spatial_hash=True)
        self.wall_list = arcade.tilemap.process_layer(map_object=my_map,
                                                      layer_name=platform_layer_name,
                                                      scaling=TILE_SCALING,
                                                      use_spatial_hash=True)

        # Set the background color
        if my_map.background_color:
            arcade.set_background_color(my_map.background_color)

        # Create "physic engine"
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite, self.wall_list, GRAVITY, self.ladder_list)

        # Timers
        self.total_time = 0.0
    # =======================

    # Draw sprites and information
    # ================
    def on_draw(self):
        """ Render the screen. """

        # Clear the screen to the background color
        arcade.start_render()

        # Draw our sprites
        self.wall_list.draw()
        self.background_list.draw()
        self.foreground_list.draw()
        self.dont_touch_list.draw()
        self.trampoline_list.draw()
        self.player_list.draw()
        self.enemy_list.draw()
        self.ladder_list.draw()
        self.coin_list.draw()
        self.explosion_list.draw()
        self.bullet_list.draw()
        self.bullet_enemy_list.draw()

        # Calculates minutes and seconds
        minutes = int(self.total_time) // 60
        seconds = int(self.total_time) % 60

        # Draw Timer, Score and Life on the screen (don't put it before "draw our sprites")
        time_text = f"Time: {minutes:02d}:{seconds:02d}"
        arcade.draw_text(time_text, 10 + self.view_left, 30 + self.view_bottom, arcade.color.BLACK, 20)

        score_text = f"Score: {self.score}"
        arcade.draw_text(score_text, 10 + self.view_left, 10 + self.view_bottom, arcade.csscolor.WHITE, 18)

        life_text = f"Life: {self.life}"
        arcade.draw_text(life_text, 10 + self.view_left, 600 + self.view_bottom, arcade.csscolor.WHITE, 18)
    # ================================================

    # When we use the mouse
    # ================================================
    def on_mouse_press(self, x, y, button, modifiers):
        """ Called whenever the mouse button is clicked
        """

        # create a bullet with sound
        bullet = arcade.Sprite(":resources:images/space_shooter/laserBlue01.png", SPRITE_LASER_SCALING)
        arcade.sound.play_sound(self.gun_sound)

        # POSITION THE BULLET
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y
        bullet.center_x = start_x
        bullet.center_y = start_y

        # mouse destination
        dest_x = x + self.view_left
        dest_y = y + self.view_bottom

        # Compute the correct angle
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        # Angle the bullet sprite
        bullet.angle = math.degrees(angle)
        print(f"Bullet angle: {bullet.angle: .2f}")

        bullet.change_x = math.cos(angle)*BULLET_SPEED
        bullet.change_y = math.sin(angle)*BULLET_SPEED

        # Add the bullet to the appropriate list
        self.bullet_list.append(bullet)
    # =====================================

    # When we use the keyboard
    # =====================================
    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        # Add jump and climb up the ladder
        if key == arcade.key.UP or key == arcade.key.W or key == arcade.key.SPACE:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
            elif self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)
        # Climb dow the ladder
        elif key == arcade.key.DOWN or key == arcade.key.S:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED
        # Add horizontal movement
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
    # =========================================================

    # When we release the keyboard
    # =========================================================
    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0
        elif key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = 0
        elif key == arcade.key.DOWN or key == arcade.key.S:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = 0
    # =========================================

    # Game changing
    # =========================================
    def on_update(self, delta_time):
        """ Movement and game logic """

        # update time
        self.total_time += delta_time

        # Move the player with the physics engine
        self.physics_engine.update()
        self.explosion_list.update()
        self.frame_count +=1

        for enemy in self.enemy_list:
            # Position to start at the enemy current location
            start_xx = enemy.center_x
            start_yy = enemy.center_y

            # Get the destination location for the bullet
            dest_xx = self.player_sprite.center_x
            dest_yy = self.player_sprite.center_y

            # Math to calculate how to get bullet to the destination
            xx_diff = dest_xx - start_xx
            yy_diff = dest_yy - start_yy
            angle = math.atan2(yy_diff, xx_diff)

            # Set the enemy to the face of the player
            enemy.angle = math.degrees(angle) - 180

            # Shoot every 90 frames changes and only if close to the player
            if abs(xx_diff) < 600 and abs(yy_diff) < 450:
                if self.frame_count % 90 == 0:
                    bullet_enemy = arcade.Sprite(":resources:images/space_shooter/laserBlue01.png")
                    bullet_enemy.center_x = start_xx
                    bullet_enemy.center_y = start_yy

                    # Angle the bullet sprite
                    bullet_enemy.angle = math.degrees(angle)

                    # Take into account the angle, calculate our change_x and y
                    bullet_enemy.change_x = math.cos(angle) * BULLET_SPEED
                    bullet_enemy.change_y = math.sin(angle) * BULLET_SPEED

                    self.bullet_enemy_list.append(bullet_enemy)

        # Get rid of the bullet_enemy when it flies of the screen
        if not self.game_over:
            self.enemy_list.update()

            for enemy in self.enemy_list:
                if len(arcade.check_for_collision_with_list(enemy, self.wall_list)) > 0:
                    enemy.change_x *= -1
                elif enemy.boundary_left is not None and enemy.left < enemy.boundary_left:
                    enemy.change_x *= -1
                elif enemy.boundary_right is not None and enemy.right > enemy.boundary_right:
                    enemy.change_x *= -1

        # See if we reach a coin
        coin_hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                             self.coin_list)

        # Loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:
            coin.remove_from_sprite_lists()
            arcade.play_sound(self.collect_coin_sound)
            # Increase the score
            self.score += 1

        # Bullet
        self.bullet_list.update()

        for bullet in self.bullet_enemy_list:
            hit_wall_enemy = arcade.check_for_collision_with_list(bullet, self.wall_list)
            if len(hit_wall_enemy) > 0:
                arcade.play_sound(self.gun_sound)
                bullet.remove_from_sprite_lists()

        for bullet in self.bullet_list:
            hit_list = arcade.check_for_collision_with_list(bullet, self.coin_list)
            hit_enemy = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            hit_trampoline = arcade.check_for_collision_with_list(bullet, self.trampoline_list)
            hit_wall = arcade.check_for_collision_with_list(bullet, self.wall_list)

            # Collision with the wall for player bullet
            if len(hit_wall) > 0:
                arcade.play_sound(self.gun_sound)
                bullet.remove_from_sprite_lists()

            if len(hit_list) > 0:
                arcade.play_sound(self.gun_sound)
                bullet.remove_from_sprite_lists()

            for coin in hit_list:
                coin.remove_from_sprite_lists()
                arcade.play_sound(self.collect_coin_sound)
                self.score += 1

            if len(hit_enemy) > 0:
                # Make an explosion when the enemy is destroyed
                explosion = Explosion(self.explosion_texture_list)
                # Move it to the location of the enemy
                explosion.center_x = hit_enemy[0].center_x
                explosion.center_y = hit_enemy[0].center_y
                # Call update
                explosion.update()
                self.explosion_list.append(explosion)

                arcade.play_sound(self.gun_sound)
                bullet.remove_from_sprite_lists()

            for enemy in hit_enemy:
                arcade.sound.play_sound(self.hit_sound)
                enemy.remove_from_sprite_lists()

            # if the bullet flies off screen, remove it
            if bullet.bottom > self.width+self.view_bottom or bullet.top <0 or bullet.right <0 or bullet.left > self.width+self.view_left:
                bullet.remove_from_sprite_lists()

        # Manage Scrolling
        # Track if we need to change the viewport
        changed = False

        # Kill the player if he falls out of the map
        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y
            # set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed = True
            arcade.play_sound(self.game_over)

            # Lose 3 points if you die (no negative value)
            if self.score > 2:
                self.score -= 3
            else: self.score = 0

            if self.life > 1:
                self.life -= 1
            else: self.life = 0

        # Kill the player if he touches something dangerous
        if arcade.check_for_collision_with_list(self.player_sprite, self.dont_touch_list):
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

            # Set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed = True
            arcade.play_sound(self.game_over)

            if self.score > 2:
                self.score -= 3
            else: self.score = 0

            if self.life > 1:
                self.life -= 1
            else: self.life = 0

        if arcade.check_for_collision_with_list(self.player_sprite, self.trampoline_list):
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 20

        # Kill the player if he is touched by an enemy bullet
        self.bullet_enemy_list.update()
        for bullet_enemy in self.bullet_enemy_list:

            hit_enemy_player = arcade.check_for_collision_with_list(bullet_enemy, self.player_list)

            if len(hit_enemy_player) > 0:
                arcade.play_sound(self.gun_sound)
                bullet_enemy.remove_from_sprite_lists()

                if bullet_enemy.bottom > self.width + self.view_bottom or bullet_enemy.top < 0 or bullet_enemy.right < 0 or bullet_enemy.left > self.width + self.view_left:
                    bullet_enemy.remove_from_sprite_lists()

                self.player_sprite.center_x = PLAYER_START_X
                self.player_sprite.center_y = PLAYER_START_Y

                # Set the camera to the start
                self.view_left = 0
                self.view_bottom = 0
                changed = True
                arcade.play_sound(self.game_over)
                if self.score > 2:
                    self.score -= 3
                else: self.score = 0
                if self.life > 1:
                    self.life -= 1
                else:
                    self.life = 0

        # Restart the game when you have no more life
        if self.life == 0:
            # Restart to the first level
            self.level = 1
            # load the first level
            self.setup(self.level)
            # Set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed = True

        # See if the user got the end of the level
        if self.player_sprite.center_x >= self.end_of_map:
            # Advance to the next level
            self.level += 1
            # load the next level
            self.setup(self.level)
            # Set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed = True

        self.player_list.update()
        self.player_list.update_animation()

        # Scroll left
        left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed = True

        # Scroll right
        right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed = True

        # Scroll up
        top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed = True

        # Scroll down
        bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.player_sprite.bottom
            changed = True

        if changed:
            # Only scroll to integers. Otherwise we end up with pixels that don't line up on the screen
            self.view_bottom = int(self.view_bottom)
            self.view_left = int(self.view_left)

            # Do the scrolling
            arcade.set_viewport(self.view_left,
                                SCREEN_WIDTH + self.view_left,
                                self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)
# ======================================================================================================================

# Main
# ======================================================================================================================
def main():
    """ Main method """
    window = MyGame()
    window.setup(window.level)
    arcade.run()

if __name__ == "__main__":
    main()
# ======================================================================================================================
