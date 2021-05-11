const { Client, Intents, Message } = require('discord.js');
const client = new Client({ intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES] });

client.on('ready', () => {
    console.log(`Logged in as ${client.user.tag}.`);
});

client.on('message', msg => {
    if (msg.content == 'Hello') {
        msg.channel.send('world!');
    }
});


client.login();