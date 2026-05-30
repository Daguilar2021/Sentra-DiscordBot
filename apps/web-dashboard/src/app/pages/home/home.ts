  import { Component, inject } from '@angular/core';
  import { FeatureCard } from '../../feature-card/feature-card';
  import { DiscordService } from '../../services/discord';

  interface InviteUrlObserver {
    next: (url: string) => void;
    error: (err: unknown) => void;
  }

  @Component({
    selector: 'app-home',
    imports: [FeatureCard],
    templateUrl: './home.html',
    styleUrl: './home.css',
  })
  export class Home {
    private discordService: DiscordService = inject(DiscordService);

    connectDiscord(): void {
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

    // redirect to documentation page
    learnMore(): void {
      window.location.href = '/documentation';
    }
  }
