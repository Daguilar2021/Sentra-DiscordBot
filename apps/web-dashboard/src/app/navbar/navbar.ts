import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DiscordService } from '../services/discord';

interface InviteUrlObserver {
    next: (url: string) => void;
    error: (err: unknown) => void;
  }

@Component({
  selector: 'app-navbar',
  imports: [RouterLink],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css'
})
export class Navbar {
  private discordService: DiscordService = inject(DiscordService);


  connectDiscord() {
    const observer: InviteUrlObserver = {
        next: (url: string) => {
          window.location.href = url;
        },
        error: (err: unknown) => {
          console.error('Failed to get invite URL:', err);
        }
      };

      this.discordService.getInviteUrl().subscribe(observer);
  }
}
