import datetime
import asyncio
import csv
import os

async def add_reminder(ctx, date, time, message):
    try:
        # Check if the date and time are in the correct format
        try:
            reminder_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            await ctx.response.send_message("Invalid date or time format. Please use **YYYY-MM-DD** for the date and **HH:MM** for the time.")
            return
        
        # Write the reminder to a CSV file
        with open('reminders.csv', 'a', newline='', encoding='utf-8') as csvfile:
            reminder_writer = csv.writer(csvfile)
            reminder_writer.writerow([reminder_datetime, message, ctx.channel.id])
            
            await ctx.response.send_message(f"**Reminder set:**\nMessage: `{message}`\nDate and Time: `{reminder_datetime.strftime('%Y-%m-%d %H:%M')}`")
    except Exception as e:
        await ctx.response.send_message("Could not set the reminder. Please try again.")
        
        
async def handle_reminders(client):
    while True:
        try:
            if os.path.exists('reminders.csv'):
                # Read reminders from the CSV file
                with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                    reminder_reader = csv.reader(csvfile)
                    reminders = list(reminder_reader)

                for row in reminders[1:]:
                    reminder_datetime = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                    message = row[1]
                    channel_id = int(row[2])
                    
                    # Calculate the time difference between now and the reminder time
                    now = datetime.datetime.now()
                    time_difference = (reminder_datetime - now).total_seconds()
                    
                    if time_difference > 0:
                        if time_difference > 15 * 60:
                            # Calculate the time difference for the 15-minute warning
                            warning_time_difference = time_difference - 15 * 60
                            
                            # Wait until 15 minutes before the reminder time
                            await asyncio.sleep(warning_time_difference)
                            # Send the 15-minute warning
                            channel = client.get_channel(channel_id)
                            await channel.send(f"@everyone **Reminder:** `{message}` in 15 minutes!")
                            
                            # Wait until the actual reminder time
                            await asyncio.sleep(15 * 60)
                        else:
                            # Wait until the actual reminder time
                            await asyncio.sleep(time_difference)
                        
                        # Send the reminder message
                        channel = client.get_channel(channel_id)
                        await channel.send(f"@everyone **Reminder:** `{message}`")
                        
                        # Remove the reminder from the CSV file
                        reminders.remove(row)
                        with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                            reminder_writer = csv.writer(csvfile)
                            reminder_writer.writerows(reminders)
            else:
                # Create the CSV file if it doesn't exist
                with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                    reminder_writer = csv.writer(csvfile)
                    reminder_writer.writerow(["datetime", "message", "channel_id"])
                    
            # Wait for 60 seconds before checking for reminders again
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error handling reminders: {e}")
        
            
async def list_reminders(ctx):
    try:
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            if len(reminders) > 1:
                reminder_list = "\n".join([f"**{index}.** Date and Time: `{row[0][:16]}`\nMessage: `{row[1]}`" for index, row in enumerate(reminders[1:], start=1)])
                await ctx.response.send_message(f"**Upcoming Reminders:**\n{reminder_list}")
            else:
                await ctx.response.send_message("No upcoming reminders.")
        else:
            await ctx.response.send_message("No upcoming reminders.")
    except Exception as e:
        await ctx.response.send_message("Could not retrieve reminders. Please try again.")
        

async def delete_reminder(ctx, index):
    try:
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            if 1 <= index < len(reminders):
                deleted_reminder = reminders.pop(index)
                with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                    reminder_writer = csv.writer(csvfile)
                    reminder_writer.writerows(reminders)
                await ctx.response.send_message(f"**Deleted reminder:**\nDate and Time: `{deleted_reminder[0][:16]}`\nMessage: `{deleted_reminder[1]}`")
            else:
                await ctx.response.send_message("Invalid index. Please provide a valid reminder index.")
        else:
            await ctx.response.send_message("No reminders to delete.")
    except Exception as e:
        await ctx.response.send_message("Could not delete reminder. Please try again.")
        
        
async def delete_all_reminders(ctx):
    try:
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            for index in range(len(reminders) - 1, 0, -1):
                await delete_reminder(ctx, index)
                
            await ctx.response.send_message("All reminders have been deleted.")
        else:
            await ctx.response.send_message("No reminders to delete.")
    except Exception as e:
        await ctx.response.send_message("Could not delete all reminders. Please try again.")
        
        
async def modify_reminder(ctx, index, new_date=None, new_time=None, new_message=None):
    try:
        if os.path.exists('reminders.csv'):
            with open('reminders.csv', 'r', encoding='utf-8') as csvfile:
                reminder_reader = csv.reader(csvfile)
                reminders = list(reminder_reader)
                
            if 1 <= index < len(reminders):
                current_reminder = reminders[index]
                current_datetime = datetime.datetime.strptime(current_reminder[0], "%Y-%m-%d %H:%M:%S")
                
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
                
                new_message = new_message if new_message else current_reminder[1]
                
                reminders[index] = [current_datetime, new_message, current_reminder[2]]
                with open('reminders.csv', 'w', newline='', encoding='utf-8') as csvfile:
                    reminder_writer = csv.writer(csvfile)
                    reminder_writer.writerows(reminders)
                await ctx.response.send_message(f"**Modified reminder:**\nDate and Time: `{current_datetime.strftime('%Y-%m-%d %H:%M')}`\nMessage: `{new_message}`")
            else:
                await ctx.response.send_message("Invalid index. Please provide a valid reminder index.")
        else:
            await ctx.response.send_message("No reminders to modify.")
    except Exception as e:
        await ctx.response.send_message("Could not modify reminder. Please try again.")
