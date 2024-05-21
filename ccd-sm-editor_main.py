import math
import random
import os
import json
# pip install Pillow
import PIL
os.environ[ 'PYGAME_HIDE_SUPPORT_PROMPT' ] = '1'  # Really pygame?
# pip install pygame
import pygame
# pip install thorpy
import thorpy
import workspace_settings


def main():
    pygame.init()
    pygame.display.set_caption( "Crystal Clear Design - State Machine Editor" )
    icon = pygame.image.load( "CCD_Logo_32x32_on_trans.png" )
    pygame.display.set_icon( icon )
    wksp_settings = workspace_settings.workspace_settings( pygame )
    app_size = wksp_settings.get_app_size()
    screen = pygame.display.set_mode( size = app_size, flags = pygame.RESIZABLE )
    screen.fill( "gray" )
    # Bind screen to gui elements and set theme.
    thorpy.set_default_font( "arial", 16 )
    thorpy.init( screen, thorpy.theme_classic )

    menu_buttons = [
        thorpy.Button( "File" ),
        thorpy.Button( "Edit" ),
        thorpy.Button( "Exit" ) ]
    menu_group = thorpy.Group( menu_buttons, mode = "h", margins = ( 0, 0 ), gap = 0, align = "top" )
    #menu_group = thorpy.Box(menu_buttons, sort_immediately = False )
    #menu_group.sort_children( mode = "grid", nx = 100, ny = 1 )
    #menu_group.stick_to( screen, "left", "left", delta = ( 0, 0 ) )
    menu_group.set_topleft( 0, 0 )

    tool_buttons = [
        thorpy.Button( "Select" ),
        #button.set_topleft( 0, 0 )
        thorpy.Button( "Start" ),
        thorpy.Button( "State" ),
        thorpy.Button( "Transition" ),
        thorpy.Button( "Stop" ) ]
    tool_group = thorpy.Group( tool_buttons, margins = ( 0, 0 ), gap = 0, nx = 1, ny = "auto", align = "left" )
    #tool_group = thorpy.TitleBox("Tools", tool_buttons, sort_immediately = False, align = "top" )
    #tool_group.sort_children( mode = "grid", nx = 1, ny = 100 )
    #tool_group.stick_to( screen, "top", "top", delta = ( 0, 0 ) )

    app_group = thorpy.Group( [ menu_group, tool_group ], gap = 0, align = "left" )
    #app_group.stick_to( screen, "left", "left", delta = ( 0, 0 ) )

    def main_process_input():
        print("Foo")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
            elif event.type == pygame.VIDEORESIZE:
                wksp_settings.set_app_size( event.w, event.h )
                #scrsize = event.size
                #screen = pygame.display.set_mode(scrsize,RESIZABLE)

        keys = pygame.key.get_pressed()
        '''
        if keys[pygame.K_w]:
            player_pos.y -= 300 * dt
        if keys[pygame.K_s]:
            player_pos.y += 300 * dt
        if keys[pygame.K_a]:
            player_pos.x -= 300 * dt
        if keys[pygame.K_d]:
            player_pos.x += 300 * dt
            '''
        if keys[pygame.K_ESCAPE]:
            exit = True
            
        # fill the screen with a color to wipe away anything from last frame.
        screen.fill( "white" )

    app_group.func_before = main_process_input
    player = app_group.get_updater( fps = 60 )
    player.launch()
    
    """
    clock = pygame.time.Clock()
    exit = False
    while ( not exit ):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit = True
            elif event.type == pygame.VIDEORESIZE:
                wksp_settings.set_app_size( event.w, event.h )
                #scrsize = event.size
                #screen = pygame.display.set_mode(scrsize,RESIZABLE)

        keys = pygame.key.get_pressed()
        '''
        if keys[pygame.K_w]:
            player_pos.y -= 300 * dt
        if keys[pygame.K_s]:
            player_pos.y += 300 * dt
        if keys[pygame.K_a]:
            player_pos.x -= 300 * dt
        if keys[pygame.K_d]:
            player_pos.x += 300 * dt
            '''
        if keys[pygame.K_ESCAPE]:
            exit = True
            
        # fill the screen with a color to wipe away anything from last frame.
        screen.fill( "white" )

        # flip() the display to put your work on screen
        pygame.display.flip()

        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-independent physics.
        dt = clock.tick( 60 ) / 1000
    """

    # Save changes to the workspace.
    wksp_settings.sync_to_disk()
    
    pygame.quit()
    

if __name__ == "__main__":
    main()

