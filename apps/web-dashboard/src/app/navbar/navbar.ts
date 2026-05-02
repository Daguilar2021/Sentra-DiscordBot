import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { DiscordService } from '../services/discord';

@Component({
  selector: 'app-navbar',
  imports: [RouterLink],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css'
})
export class Navbar {
  private discordService = inject(DiscordService);

  connectDiscord() {
    this.discordService.getInviteUrl().subscribe(url => {
      window.open(url, '_blank');
    });
  }
}
