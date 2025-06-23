# Copyright (C) 2023, Roman V. M.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources/lib'))

from urllib.parse import urlencode, parse_qsl
import hashlib
import datetime

import xbmc # type: ignore
import xbmcgui # type: ignore
import xbmcplugin # type: ignore
import xbmcaddon # type: ignore
from xbmcaddon import Addon # type: ignore
from xbmcvfs import translatePath # type: ignore

import requests
import bs4
import json
import pytubefix  # Replace pytube with putubefix
from resources.lib.utils import extract_video_id, is_youtube_plugin_installed


# Get the plugin url in plugin:// notation.
URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])
# Get addon base path
ADDON_PATH = translatePath(Addon().getAddonInfo('path'))
ICONS_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'icons')
FANART_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'fanart')
POSTER_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'posters')


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(URL, urlencode(kwargs))


def main_menu():
    list_item = xbmcgui.ListItem(label='The WOD')
    # Set the icon and fanart for the list item
    info_tag = list_item.getVideoInfoTag()
    info_tag.setMediaType('project')
    info_tag.setTitle('The WOD')
    info_tag.setPlot("Today's Workout of the Day")
    url = get_url(action='display_workout', date=datetime.date.today().strftime('%y%m%d'))
    is_folder = True
    # Add the item to the directory
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    
    list_item = xbmcgui.ListItem(label='The Movements')
    # Set the icon and fanart for the list item
    info_tag = list_item.getVideoInfoTag()
    info_tag.setMediaType('project')
    info_tag.setTitle('Movements')
    info_tag.setPlot('Movements')
    url = get_url(action='movements')
    is_folder = True
    # Add the item to the directory
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    list_item = xbmcgui.ListItem(label='The Workouts')
    # Set the icon and fanart for the list item
    info_tag = list_item.getVideoInfoTag()
    info_tag.setMediaType('project')
    info_tag.setTitle('Workouts')
    info_tag.setPlot('Workouts')
    url = get_url(action='workouts')
    is_folder = True
    # Add the item to the directory
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(HANDLE)    


def list_movements():
    """
    List movements from the CrossFit website.
    """
    xbmcplugin.setPluginCategory(HANDLE, 'Movements')
    xbmcplugin.setContent(HANDLE, 'videos')

    url = 'https://www.crossfit.com/crossfit-movements'
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')

    # Find the h2 with the exact text
    header = soup.find('h2', string="More CrossFit Movements")
    if header:
        parent_div = header.find_parent('div')
        if parent_div:
            lists = parent_div.find_all(['ul', 'ol'])
            all_items = []
            for lst in lists:
                items = lst.find_all('li')
                all_items.extend(items)
            for item in all_items:
                label = item.text.strip()
                link = item.find('a')
                list_item = xbmcgui.ListItem(label=label)
                list_item.setInfo('video', {'title': label})
                list_item.setProperty('IsPlayable', 'true' if link and 'href' in link.attrs else 'false')
                if link and 'href' in link.attrs:
                    # Pass the video URL to the play_movement action
                    url = get_url(action='play_movement', video_url=link['href'])
                    is_folder = False
                else:
                    url = ''
                    is_folder = False
                xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
            xbmcplugin.endOfDirectory(HANDLE)
        else:
            print("Parent div not found.")
    else:
        print("Header 'More CrossFit Movements' not found.")


def list_workouts():
    """
    List workouts from the CrossFit website.
    """
    xbmcplugin.setPluginCategory(HANDLE, 'Workouts')
    xbmcplugin.setContent(HANDLE, 'videos')

    # Just list the last 20 workouts for now
    for i in range(0, 19):
        wod_date = (datetime.date.today() - datetime.timedelta(days=i))
        # Format the date as 'yymmdd' - this is the format used in the CrossFit WOD URLs and titles
        datestamp = wod_date.strftime('%y%m%d')
        humandate = datetime.date.strftime(wod_date, '%A, %B %d, %Y')
        url = f'https://www.crossfit.com/{datestamp}'
        list_item = xbmcgui.ListItem(label=f'{datestamp} - {humandate}')
        is_folder = True
        # Set the title to be formatted as 'yymmdd - Day of the Week, Month Day, Year'
        list_item.setInfo('video', {'title': f'{datestamp} - {humandate}'})
        list_item.setProperty('IsPlayable', 'false')
        # Use the date as a parameter to display the workout
        url = get_url(action='display_workout', date=datestamp)
        # Add the item to the directory
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(HANDLE)

def display_workout(date):
    """
    Display workouts from the CrossFit website.
    """

    xbmcplugin.setPluginCategory(HANDLE, 'Workout')
    xbmcplugin.setContent(HANDLE, 'videos')

    # Create the URL for the workout page
    url = f'https://www.crossfit.com/{date}'

    response = requests.get(f'https://www.crossfit.com/{date}')
    soup = bs4.BeautifulSoup(response.text, 'html.parser')

    xbmc.log(f"Displaying workout for {date}", xbmc.LOGINFO)

    # Check if the response was successful
    if response.status_code != 200:
        xbmcgui.Dialog().notification('Error', f'Failed to fetch workout for {date}', xbmcgui.NOTIFICATION_ERROR)
        xbmc.log(f"Failed to fetch workout for {date} - status code: {response.status_code}", xbmc.LOGERROR)
        return

    # Find the 'article' element with the class 'wod'
    article = soup.find('article')
    if not article:
        xbmcgui.Dialog().notification('Error', f'No workout found for {date}', xbmcgui.NOTIFICATION_ERROR)
        xbmc.log(f"No workout found for {date} - missing 'article' element", xbmc.LOGERROR)
        xbmc.log(f"Response content: {response.text}", xbmc.LOGINFO)
        return
    
    workout_text = article.get_text(strip=False, separator='\n')
    workout_item = xbmcgui.ListItem(label=f'Workout for {date}')
    workout_item.setInfo('video', {
        'title': f'Workout for {date}',
        'plot': workout_text,
    })
    workout_item.setProperty('IsPlayable', 'true')
    # Pass the workout text as a parameter (URL-encoded)
    url = get_url(action='show_workout_text', text=workout_text)
    xbmcplugin.addDirectoryItem(HANDLE, url, workout_item, isFolder=False)

    # Add a simulated divider
    divider_item = xbmcgui.ListItem(label='----------------')
    divider_item.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(HANDLE, '', divider_item, isFolder=False)

    # Find the <p> that contains <strong>Resources:</strong>
    for p in article.find_all('p'):
        strong_tag = p.find('strong', string='Resources:')
        if strong_tag:
            # If we found the Resources tag, we can stop searching
            xbmc.log("Found 'Resources:' section", xbmc.LOGINFO)
            resources_section = p
            break
    else:
        # If we didn't find the Resources tag, log it
        xbmc.log("No 'Resources:' section found in the article", xbmc.LOGINFO)
        resources_section = None
        return

    resource_links = []
    if resources_section:
        resource_links = resources_section.find_all('a')
    for resource_link in resource_links:
        xbmc.log(f"Processing resource link: {resource_link}", xbmc.LOGINFO)
        href = resource_link.get('href', '')
        label = resource_link.text.strip()

        # Determine link type
        if 'youtube.com' in href or 'youtu.be' in href:
            link_type = 'youtube'
        elif 'crossfit.com/essentials' in href or '/essentials/' in href:
            link_type = 'essentials'
        else:
            link_type = 'other'
            xbmc.log(f"Found {link_type} link: {label} ({href})", xbmc.LOGINFO)
            xbmc.log(f"Skipping non-youtube non-essentials link", xbmc.LOGINFO)
            continue  # Skip non-YouTube and non-essentials links

        xbmc.log(f"Found {link_type} link: {label} ({href})", xbmc.LOGINFO)

        list_item = xbmcgui.ListItem(label=label)
        list_item.setInfo('video', {'title': label})
        list_item.setProperty('IsPlayable', 'true')

        # Set the action based on link type
        if link_type == 'youtube':
            # For YouTube links, we can play them directly
            # list_item.setProperty('path', href)
            url = get_url(action='play_youtube', video_url=href)
            is_folder = False
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
        elif link_type == 'essentials':
            # For essentials links, we will use the play_movement action
            url = get_url(action='play_movement', video_url=href)
            is_folder = False
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
        else:
            # For other links, we just display them as non-playable items
            url = href
            is_folder = False


    xbmcplugin.endOfDirectory(HANDLE)


def play_movement(video_url):
    """
    Resolve and play the movement video.
    """
    xbmc.log(f"Playing movement video: {video_url}", xbmc.LOGINFO)

    response = requests.get(video_url)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')

    # Find the first iframe with a YouTube link in the src
    iframe = soup.find('iframe', src=lambda s: s and 'youtube.com' in s)
    if iframe and 'src' in iframe.attrs:
        youtube_url = iframe['src']
        # Some YouTube embed URLs may start with "//", so normalize if needed
        if youtube_url.startswith('//'):
            youtube_url = 'https:' + youtube_url
        elif youtube_url.startswith('/'):
            youtube_url = 'https://www.crossfit.com' + youtube_url

        xbmc.log(f"Found YouTube URL: {youtube_url}", xbmc.LOGINFO)

        play_youtube(youtube_url)
    else:
        # fallback: just use the original page URL
        list_item = xbmcgui.ListItem(path=video_url)
        list_item.setProperty('IsPlayable', 'true')
        xbmcplugin.setResolvedUrl(HANDLE, True, list_item)


def play_youtube(video_url):
    """
    Play a YouTube video using the provided video URL.
    """
    xbmc.log(f"Playing directly-linked YouTube video: {video_url}", xbmc.LOGINFO)
    
    addon = xbmcaddon.Addon()
    use_youtube_plugin = addon.getSettingBool('use_youtube_plugin')
    if use_youtube_plugin:
        if is_youtube_plugin_installed():
            # Play via YouTube plugin
            plugin_url = f'plugin://plugin.video.youtube/play/?video_id={extract_video_id(video_url)}'
            list_item = xbmcgui.ListItem(path=plugin_url)
            list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.setResolvedUrl(HANDLE, True, list_item)
            return
        else:
            xbmcgui.Dialog().notification(
                'YouTube Plugin Not Installed',
                'Falling back to direct playback.',
                xbmcgui.NOTIFICATION_WARNING
            )
    # Fallback to direct stream (pytubefix)
    try:
        yt = pytubefix.YouTube(video_url)
        stream = yt.streams.order_by('resolution').desc().first()
        if stream:
            resolved_url = stream.url
        else:
            resolved_url = video_url  # fallback
    except Exception as e:
        xbmc.log(f"Error resolving YouTube URL: {e}", xbmc.LOGERROR)
        resolved_url = video_url

    xbmc.log(f"Resolved YouTube URL: {resolved_url}", xbmc.LOGINFO)
    list_item = xbmcgui.ListItem(path=resolved_url)
    list_item.setProperty('IsPlayable', 'true')
    xbmcplugin.setResolvedUrl(HANDLE, True, list_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    xbmc.log(f"ROUTER params={params}", xbmc.LOGINFO)
    # Check the parameters passed to the plugin
    if not params:
        # If the plugin is called from Kodi UI without any parameters,
        # display the main menu of options
        main_menu()
    elif params['action'] == 'wod':
        date = datetime.date.today().strftime('%y%m%d')
        display_workout(date)
    elif params['action'] == 'movements':
        list_movements()
    elif params['action'] == 'workouts':
        list_workouts()
    elif params['action'] == 'display_workout':
        # Display the workout for the given date
        if 'date' in params:
            display_workout(params['date'])
        else:
            raise ValueError('No date provided for display_workout action!')
    elif params['action'] == 'play_movement':
        play_movement(params['video_url'])
    elif params['action'] == 'play_youtube':
        play_youtube(params['video_url'])
    elif params['action'] == 'show_workout_text':
        show_workout_text(params['text'])
    else:
        # If the provided paramstring does not contain a supported action
        # we raise an exception. This helps to catch coding errors,
        # e.g. typos in action names.
        raise ValueError(f'Invalid paramstring: {paramstring}!')


def show_workout_text(text):
    """
    Show the workout text in a popup dialog.
    """
    xbmcgui.Dialog().textviewer('Workout Details', text)


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
