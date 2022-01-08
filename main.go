package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/bwmarrin/discordgo"
)

func messageHandler(s *discordgo.Session, m *discordgo.MessageCreate) {
	// Ignore all messages from the bot itself
	if m.Author.ID == s.State.User.ID {
		return
	}

	// Parse the message
	message := strings.Split(m.Content, " ")
	baseCommand := message[0]

	switch baseCommand {
	case "hello":
		s.ChannelMessageSend(m.ChannelID, "Hey!")
	}

}

func main() {
	discord, err := discordgo.New("Bot " + os.Getenv("DISCORD_HEY_MARK_CLIENT_SECRET"))
	if err != nil {
		log.Fatalf("error initializing bot: %v", err)
	}

	// Discord message handler
	discord.AddHandler(messageHandler)

	// Intent to only look at chat messages
	discord.Identify.Intents = discordgo.IntentsGuildMessages

	// Open a websocket connection to Discord
	err = discord.Open()
	if err != nil {
		log.Fatalf("error establishing websocket connection to Discord: %v", err)
	}

	// Wait until CTRL+C or SIGTERM
	fmt.Println("HeyMark is running. Press CTRL+C to exit.")
	sc := make(chan os.Signal, 1)
	signal.Notify(sc, syscall.SIGINT, syscall.SIGTERM, os.Interrupt)
	<-sc

	// Close Discord session
	discord.Close()
}
