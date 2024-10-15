import datetime
import asyncio
import csv
import os
import discord

client = None
reminder_tasks = []

async def add_reminder(ctx, date, time, title, message, channel_name=None):
    try:
        # Check if the date and time are in the correct format
        try:
            reminder_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").astimezone()
        except ValueError:
            await ctx.response.send_message("Invalid date or time format. Please use **YYYY-MM-DD** for the date and **HH:MM** for the time.")
            return
        
        # Determine the channel to send the reminder
        if channel_name:
            channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
            if not channel:
                await ctx.response.send_message(f"Channel `{channel_name}` not found. Please provide a valid channel name.")
                return
        else:
            channel = discord.utils.get(ctx.guild.text_channels, name="reminders")
            if not channel:
                channel = ctx.guild.text_channels[0]
        
        # Write the reminder to a CSV file
        with open('reminders.csv', 'a', newline='', encoding='utf-8') as csvfile:
            reminder_writer = csv.writer(csvfile)
            reminder_writer.writerow([reminder_datetime.strftime('%Y-%m-%d %H:%M'), title, message, channel.id, ctx.guild.id])
        
        # Read and sort reminders
        with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
            reminder_reader = csv.reader(csvfile)
            reminders = list(reminder_reader)
        
        reminders = [reminders[0]] + sorted(reminders[1:], key=lambda row: datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M"))
        
        # Write sorted reminders back to the CSV file
        with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
            reminder_writer = csv.writer(csvfile)
            reminder_writer.writerows(reminders)
        
        await ctx.response.send_message(f"**Reminder set:**Title: `{title}`\nMessage: `{message}`\nDate and Time: `{reminder_datetime.strftime('%Y-%m-%d %H:%M')}`\nChannel: `{channel.name}`")
        
        # Create an event in the Discord server
        guild = ctx.guild
        event_name = f"Reminder: {title}"
        if len(event_name) > 100:
            event_name = event_name[:97] + "..."
        event_description = f"Reminder set for {reminder_datetime.strftime('%Y-%m-%d %H:%M')}\n {message}"
        event_start_time = reminder_datetime
        event_end_time = reminder_datetime + datetime.timedelta(hours=1)  # Set event duration to 1 hour
        # Set the event to point directly to a voice channel
        voice_channel = guild.voice_channels[0] # Default voice channel
        
        await guild.create_scheduled_event(
            name=event_name,
            description=event_description,
            start_time=event_start_time,
            end_time=event_end_time,
            entity_type=discord.EntityType.voice,
            privacy_level=discord.PrivacyLevel.guild_only,
            channel=voice_channel
        )
        
        # Restart the reminder handling process
        await handle_reminders()
    except Exception as e:
        print(f"Error setting reminder: {e}")
        if not ctx.response.is_done():
            await ctx.response.send_message("Could not set the reminder. Please try again.")
        

async def send_reminder(reminder_datetime, title, message, channel_id, guild_id):
    global client
    try:
        now = datetime.datetime.now().astimezone()
        time_difference = (reminder_datetime - now).total_seconds()
        
        if time_difference > 0:
            if time_difference > 15 * 60:
                # Calculate the time difference for the 15-minute warning
                warning_time_difference = time_difference - 15 * 60
                
                # Wait until 15 minutes before the reminder time
                await asyncio.sleep(warning_time_difference)
                # Send the 15-minute warning
                channel = client.get_channel(channel_id)
                await channel.send(f"@everyone **Reminder:** `{title}` in 15 minutes!")
                
                # Wait until the actual reminder time
                await asyncio.sleep(15 * 60)
            else:
                # Wait until the actual reminder time
                await asyncio.sleep(time_difference)
            
            # Send the reminder message
            channel = client.get_channel(channel_id)
            await channel.send(f"@everyone **Reminder:** `{title}`\n`{message}`")
            # Delete the reminder from the CSV file
            with open('reminders.csv', 'r', newline='', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            for index, row in enumerate(reminders[1:], start=1):
                if row[0] == reminder_datetime.strftime('%Y-%m-%d %H:%M') and row[1] == title and row[2] == message and int(row[3]) == channel_id and int(row[4]) == guild_id:
                    reminders.pop(index)
                    break

            with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                reminder_writer = csv.writer(csvfile)
                reminder_writer.writerow(["datetime", "title", "message", "channel_id", "guild_id"])
                reminder_writer.writerows(reminders[1:])
    except asyncio.CancelledError:
        # Handle task cancellation
        pass
    except Exception as e:
        print(f"Error sending reminder: {e}")


async def handle_reminders(bot=None):
    global reminder_tasks
    global client
    try:
        if bot:
            client = bot
        if os.path.exists('reminders.csv'):
            # Cancel any existing reminder tasks
            for task in reminder_tasks:
                task.cancel()
            reminder_tasks = []

            # Read reminders from the CSV file
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)

            for row in reminders[1:]:
                reminder_datetime = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M").astimezone()
                title = row[1]
                message = row[2]
                channel_id = int(row[3])
                guild_id = int(row[4])
                
                # Create a task for each reminder
                task = asyncio.create_task(send_reminder(reminder_datetime, title, message, channel_id, guild_id))
                reminder_tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*reminder_tasks, return_exceptions=True)
            
        else:
            # Create the CSV file if it doesn't exist
            with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                reminder_writer = csv.writer(csvfile)
                reminder_writer.writerow(["datetime", "title", "message", "channel_id", "guild_id"])
    except Exception as e:
        print(f"Error handling reminders: {e}")

            
async def list_reminders(ctx):
    try:
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            guild_reminders = [row for row in reminders[1:] if int(row[4]) == ctx.guild.id]
            
            if guild_reminders:
                reminder_list = "\n".join([
                    f"**{index}.** Date and Time: `{row[0]}`\nTitle: `{row[1]}`\nMessage: `{row[2]}`\nChannel: `{ctx.guild.get_channel(int(row[3])).name}`"
                    for index, row in enumerate(guild_reminders, start=1)
                ])
                await ctx.response.send_message(f"**Upcoming Reminders:**\n{reminder_list}")
            else:
                await ctx.response.send_message("No upcoming reminders.")
        else:
            await ctx.response.send_message("No upcoming reminders.")
    except Exception as e:
        await ctx.response.send_message("Could not retrieve reminders. Please try again.")
        print(f"Error retrieving reminders: {e}")
        

async def delete_reminder(ctx, nth_index):
    try:
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            # Filter reminders for the current guild
            guild_reminders = [row for row in reminders[1:] if int(row[4]) == ctx.guild.id]
            
            if 1 <= nth_index <= len(guild_reminders):
                # Get the actual reminder to delete
                deleted_reminder = guild_reminders[nth_index - 1]
                
                # Remove the reminder from the original list
                reminders = [row for row in reminders if row != deleted_reminder]
                
                with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                    reminder_writer = csv.writer(csvfile)
                    reminder_writer.writerows(reminders)
                    
                await ctx.response.send_message(f"**Deleted reminder:**\nDate and Time: `{deleted_reminder[0]}`\nTitle: `{deleted_reminder[1]}`\nMessage: `{deleted_reminder[2]}`")
                
                # Delete the corresponding scheduled event
                guild = ctx.guild
                event_description = f"Reminder: {deleted_reminder[2]}"
                events = await guild.fetch_scheduled_events()
                for event in events:
                    if event.description == event_description:
                        await event.delete()
                        break
                
                # Restart the reminder handling process
                await handle_reminders()
            else:
                await ctx.response.send_message("Invalid index. Please provide a valid reminder index.")
        else:
            await ctx.response.send_message("No reminders to delete.")
    except Exception as e:
        await ctx.response.send_message("Could not delete reminder. Please try again.")
        print(f"Error deleting reminder: {e}")
        
        
async def delete_all_reminders(ctx):
    try:
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            # Remove the reminders for the current guild from the original list, excluding the header row
            reminders = [reminders[0]] + [row for row in reminders[1:] if int(row[4]) != ctx.guild.id]
            
            with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                reminder_writer = csv.writer(csvfile)
                reminder_writer.writerows(reminders)
                
            await ctx.response.send_message("All reminders have been deleted.")
            
            # Delete all scheduled events for the guild
            guild = ctx.guild
            events = await guild.fetch_scheduled_events()
            for event in events:
                if event.name.startswith("Reminder:"):
                    await event.delete()
            
            # Restart the reminder handling process
            await handle_reminders()
        else:
            await ctx.response.send_message("No reminders to delete.")
    except Exception as e:
        await ctx.response.send_message("Could not delete all reminders. Please try again.")
        print(f"Error deleting all reminders: {e}")
        
        
async def modify_reminder(ctx, nth_index, new_date=None, new_time=None, new_title=None, new_message=None, new_channel_name=None):
    try:
        # Check if at least one of the optional parameters is provided
        if not new_date and not new_time and not new_title and not new_message and not new_channel_name:
            await ctx.response.send_message("Please provide at least one parameter to modify (new_date, new_time, new_title, new_message, new_channel_name).")
            return
        
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            # Filter reminders for the current guild
            guild_reminders = [row for row in reminders[1:] if int(row[4]) == ctx.guild.id]
            
            if 1 <= nth_index <= len(guild_reminders):
                # Get the actual reminder to modify
                current_reminder = guild_reminders[nth_index - 1]
                current_datetime = datetime.datetime.strptime(current_reminder[0], "%Y-%m-%d %H:%M").astimezone()
                
                if new_date:
                    try:
                        new_date_obj = datetime.datetime.strptime(new_date, "%Y-%m-%d")
                        current_datetime = current_datetime.replace(year=new_date_obj.year, month=new_date_obj.month, day=new_date_obj.day)
                    except ValueError:
                        await ctx.response.send_message("Invalid date format. Please use **YYYY-MM-DD** for the date.")
                        return
                
                if new_time:
                    try:
                        new_time_obj = datetime.datetime.strptime(new_time, "%H:%M")
                        current_datetime = current_datetime.replace(hour=new_time_obj.hour, minute=new_time_obj.minute)
                    except ValueError:
                        await ctx.response.send_message("Invalid time format. Please use **HH:MM** for the time.")
                        return
                
                new_title = new_title if new_title else current_reminder[1]
                new_message = new_message if new_message else current_reminder[2]
                
                # Determine the new channel to send the reminder
                if new_channel_name:
                    new_channel = discord.utils.get(ctx.guild.text_channels, name=new_channel_name)
                    if not new_channel:
                        await ctx.response.send_message(f"Channel `{new_channel_name}` not found. Please provide a valid channel name.")
                        return
                else:
                    new_channel = client.get_channel(int(current_reminder[3]))
                
                # Fetch the event details before modifying the CSV file
                event_name = f"Reminder: {current_reminder[1]}"
                event_start_time = datetime.datetime.strptime(current_reminder[0], "%Y-%m-%d %H:%M").astimezone()
                
                # Update the reminder in the original list
                for index, row in enumerate(reminders):
                    if row == current_reminder:
                        reminders[index] = [current_datetime.strftime('%Y-%m-%d %H:%M'), new_title, new_message, new_channel.id, current_reminder[4]]
                        break
                
                # Sort reminders by datetime
                reminders = [reminders[0]] + sorted(reminders[1:], key=lambda row: datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M"))
                
                with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                    reminder_writer = csv.writer(csvfile)
                    reminder_writer.writerows(reminders)
                await ctx.response.send_message(f"**Modified reminder:**\nDate and Time: `{current_datetime.strftime('%Y-%m-%d %H:%M')}`\nTitle: `{new_title}`\nMessage: `{new_message}`\nChannel: `{new_channel.name}`")
                
                # Modify the corresponding scheduled event
                guild = ctx.guild
                events = await guild.fetch_scheduled_events()
                for event in events:
                    if event.name == event_name and event.start_time == event_start_time:
                        new_event_name = f"Reminder: {new_title}"
                        if len(new_event_name) > 100:
                            new_event_name = new_event_name[:97] + "..."
                        await event.edit(
                            name=new_event_name,
                            description=f"Reminder set for {current_datetime.strftime('%Y-%m-%d %H:%M')} in {new_channel.name}\n{new_message}",
                            start_time=current_datetime,
                            end_time=current_datetime + datetime.timedelta(hours=1)
                        )
                        break
                
                # Restart the reminder handling process
                await handle_reminders()
            else:
                await ctx.response.send_message("Invalid index. Please provide a valid reminder index.")
        else:
            await ctx.response.send_message("No reminders to modify.")
    except Exception as e:
        await ctx.response.send_message("Could not modify reminder. Please try again.")
        print(f"Error modifying reminder: {e}")