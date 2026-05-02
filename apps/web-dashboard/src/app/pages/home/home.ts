import { Component, inject } from '@angular/core';
import { FeatureCard } from '../../feature-card/feature-card';
import { DiscordService } from '../../services/discord';

@Component({
  selector: 'app-home',
  imports: [FeatureCard],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home {
  private discordService = inject(DiscordService);

  connectDiscord() {
    this.discordService.getInviteUrl().subscribe(url => {
      window.open(url, '_blank');
    });
  }
}
