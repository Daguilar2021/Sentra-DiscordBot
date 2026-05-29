import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';

export interface DiscordCallbackResponse {
  message: string;
  discordId: string;
  guildId: string;
  email?: string;
}

@Injectable({
  providedIn: 'root'
})
export class DiscordService {
  private http = inject(HttpClient);
  private inviteUrl = `${environment.apiBaseUrl}/api/invite`;
 

  getInviteUrl(): Observable<string> {
    return this.http.get<{ url: string }>(this.inviteUrl).pipe(
      map(response => response.url)
    );
  }
}
