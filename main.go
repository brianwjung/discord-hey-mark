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

// Bot Command Prefix
var COMMAND_PREFIX = "!heymark"

func getStandings(message []string) string {
	team := strings.Join(message[2:], " ")
	output := fmt.Sprintf("Standings for %s go here.", team)
	return output
}

func getSchedule(message []string) string {
	team := strings.Join(message[2:], " ")
	output := fmt.Sprintf("Schedule for %s go here.", team)
	return output
}

func messageHandler(s *discordgo.Session, m *discordgo.MessageCreate) {
	// Ignore all messages from the bot itself
	if m.Author.ID == s.State.User.ID {
		return
	}

	// Parse the message
	message := strings.Split(strings.ToLower(m.Content), " ")

	// Check if bot command
	if message[0] == COMMAND_PREFIX {
		// Get the base command
		baseCommand := strings.ToLower(message[1])

		// Command list
		switch baseCommand {
		case "hey":
			s.ChannelMessageSend(m.ChannelID, "Hey!")
		case "watch":
			s.ChannelMessageSend(m.ChannelID, "Watch a thing!")
		case "standings":
			s.ChannelMessageSend(m.ChannelID, getStandings(message))
		case "schedule":
			s.ChannelMessageSend(m.ChannelID, getSchedule(message))
		default:
			s.ChannelMessageSend(m.ChannelID, "Unrecognized command!")
		}
	} else {
		return
	}
}

func main() {
	// Create the Discord Client
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
