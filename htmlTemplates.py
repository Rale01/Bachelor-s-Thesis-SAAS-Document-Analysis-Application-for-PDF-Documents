

bot_template = '''
<div class="chat-message bot" style = "padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; background-image: linear-gradient(to right top, #202424, #1b1e1f, #171819, #111212, #090909);">
    <div class="avatar" style = "width: 20%;">
        <img src="https://i.ibb.co/YPHsYps/image0-0.jpg" style="max-height: 85px; max-width: 85px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message" style = "width: 80%; padding: 0 1.5rem; color: #fff;">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user" style = "padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; background-image: linear-gradient(to right top, #4d0303, #3e0706, #2f0906, #210705, #0e0202);">
    <div class="avatar" style = "width: 20%;">
        <img src="https://i.ibb.co/Lt1p6G4/person.png" style="max-height: 85px; max-width: 85px; border-radius: 50%; object-fit: cover;">
    </div>    
    <div class="message" style = "width: 80%; padding: 0 1.5rem; color: #fff;">{{MSG}}</div>
</div>
'''
