import os
import sys

dir_split = os.path.abspath(os.path.dirname(__file__)).split('\\')
dirc = "\\".join(dir_split[:-1])
sys.path.insert(1, f'{dirc}')

from discord.interactions import Interaction
import discord
from discord.ext import commands

import LoadConfig

class VoteList(discord.ui.View): #익명, 중복불가투표
    def __init__(self, bot, voteName, label_id, timeout=5):
        super().__init__(timeout=timeout)
        self.set = LoadConfig.Config() #설정
        self.bot = bot
        self.channel = self.bot.get_channel(int(self.set.channel)) #누가 투표했는지 지정된 채널에 보내기 위해 필요
        self.message = None #view를 포함하고 있는 메시지

        self.voteName = voteName #x인자로 받은 투표의 이름

        self.voter_list = [] #투표에 참여한 사람의 전체 목록
        self.vote_specific_dict = { i:[] for i in label_id } #특정 대상에 투표한 사람의 목록
        self.counter = { i:0 for i in label_id } #항목별 투표 인원 수

        self.button_dict = {} #항목별 버튼
        
        for i in label_id: #view 위에 항목별 버튼 생성
            button = discord.ui.Button(label=f"{i} : 0")
            button.custom_id = i #button id를 항목명과 동일하게 설정
            button.counterLabel = 0 #button에 표시될 숫자 초기화
            self.add_item(button)
            self.button_dict[i] = button #button을 딕셔너리에 접근 가능하게 지정

    async def on_timeout(self) -> None:
        await self.message.edit(embed=discord.Embed(title=f"***{self.voteName}*** 투표가 종료되었습니다 - 투표 참가자", description=f"```{', '.join(self.voter_list)}```" , color=discord.Color.yellow()), view=None)
        await self.message.channel.send(embed = discord.Embed(title=f"[***{self.voteName}*** 투표 결과]", description=self.result_vote(), color=discord.Color.green()))

    async def updateButtonCount(self, interaction):
        #투표 오를때마다 레이블의 숫자 수정
        self.counter[interaction.data['custom_id']] += 1
        self.button_dict[interaction.data['custom_id']].counterLabel += 1
        self.button_dict[interaction.data['custom_id']].label = f"{interaction.data['custom_id']} : {self.button_dict[interaction.data['custom_id']].counterLabel}"
        await self.message.edit(view=self)

    def set_self_message(self, msg):
        self.message = msg

    def result_vote(self) -> str: #결과 포맷을 오버라이딩하여 사용
        return "None"


class VoteType1(VoteList): #중복불가, 익명
    async def interaction_check(self, interaction: Interaction) -> bool:
        #await self.channel.send(f"{interaction.user}의 참여") #누가 참여했는지, 지정한 채널에 메시지로 전달됨
        await interaction.response.defer()
        if interaction.type != discord.InteractionType.component:
            return
        
        if interaction.user.name in self.voter_list: #이미 참여한 사람이 누를 시 무시함
            return

        await self.updateButtonCount(interaction) #버튼 숫자 업데이트
        self.voter_list.append(interaction.user.name) #투표인원 전체 목록에 저장, 중복방지

    def result_vote(self) -> str:
        s = sum(self.counter.values())
        return "\n".join( (f"{i} : {self.counter[i]}표({round(self.counter[i]/s, 4)*100}%)" for i in self.counter.keys()) )

class VoteType2(VoteList): #중복불가, 실명
    async def interaction_check(self, interaction: Interaction) -> bool:
        #await self.channel.send(f"{interaction.user}의 참여") #누가 참여했는지, 지정한 채널에 메시지로 전달됨
        await interaction.response.defer()
        if interaction.type != discord.InteractionType.component:
            return
        
        if interaction.user.name in self.voter_list: #이미 참여한 사람이 누를 시 무시함
            return

        await self.updateButtonCount(interaction) #버튼 숫자 업데이트
        self.voter_list.append(interaction.user.name) #투표인원 전체 목록에 저장, 중복방지
        self.vote_specific_dict[interaction.data['custom_id']].append(interaction.user.name) #항목별 목록에 저장, 결과에 함께 출력함

    def result_vote(self) -> str:
        s = sum(self.counter.values())
        return "\n".join( (f"{i} : {self.counter[i]}표({round(self.counter[i]/s, 4)*100}%)\n```>> {', '.join(self.vote_specific_dict[i])}```" for i in self.counter.keys()) )
    

class VoteType3(VoteList): #중복가능, 익명
    async def interaction_check(self, interaction: Interaction) -> bool:
        #await self.channel.send(f"{interaction.user}의 참여") #누가 참여했는지, 지정한 채널에 메시지로 전달됨
        await interaction.response.defer()
        if interaction.type != discord.InteractionType.component:
            return
        
        if interaction.user.name in self.vote_specific_dict[interaction.data['custom_id']]: #이미 투표한 항목을 또 누를 시 무시함
            return

        await self.updateButtonCount(interaction) #버튼 숫자 업데이트
        if interaction.user.name not in self.voter_list: self.voter_list.append(interaction.user.name) #투표인원 전체 목록에 저장
        self.vote_specific_dict[interaction.data['custom_id']].append(interaction.user.name) #항목별 목록에 저장

    def result_vote(self) -> str:
        s = sum(self.counter.values())
        return "\n".join( (f"{i} : {self.counter[i]}표({round(self.counter[i]/s, 4)*100}%)" for i in self.counter.keys()) )

class VoteType4(VoteList): #중복가능, 실명
    async def interaction_check(self, interaction: Interaction) -> bool:
        #await self.channel.send(f"{interaction.user}의 참여") #누가 참여했는지, 지정한 채널에 메시지로 전달됨
        await interaction.response.defer()
        if interaction.type != discord.InteractionType.component:
            return
        
        if interaction.user.name in self.vote_specific_dict[interaction.data['custom_id']]: #이미 투표한 항목을 또 누를 시 무시함
            return

        await self.updateButtonCount(interaction) #버튼 숫자 업데이트
        if interaction.user.name not in self.voter_list: self.voter_list.append(interaction.user.name) #투표인원 전체 목록에 저장
        self.vote_specific_dict[interaction.data['custom_id']].append(interaction.user.name) #항목별 목록에 저장

    def result_vote(self) -> str:
        s = sum(self.counter.values())
        return "\n".join( (f"{i} : {self.counter[i]}표({round(self.counter[i]/s, 4)*100}%)\n```>> {', '.join(self.vote_specific_dict[i])}```" for i in self.counter.keys()) )

class Voter(commands.Cog): #커맨드로 이름 변경
    def __init__(self, bot) -> None:
        self.bot = bot
        self.set = LoadConfig.Config()
    
    @commands.command(name="vote1")
    async def sendVoteType1(self, ctx, voteName, voteTime, *labels): #채팅에 투표이름, 시간, 인자들 순서로 입력
        if self.set.command_allow_opt and (ctx.message.author.name not in self.set.command_allow):return #명령권한 설정이 되어 있는 경우 화이트리스트 확인
        view = VoteType1(self.bot, voteName, labels, int(voteTime)) #입력을 토대로 투표버튼 생성
        message = await ctx.send(embed = discord.Embed(title=voteName, color=discord.Color.yellow()), view=view)
        view.set_self_message(message)
        
    @commands.command(name="vote2")
    async def sendVoteType2(self, ctx, voteName, voteTime, *labels): #채팅에 투표이름, 시간, 인자들 순서로 입력
        if self.set.command_allow_opt and (ctx.message.author.name not in self.set.command_allow):return #명령권한 설정이 되어 있는 경우 화이트리스트 확인
        view = VoteType2(self.bot, voteName, labels, int(voteTime)) #입력을 토대로 투표버튼 생성
        message = await ctx.send(embed = discord.Embed(title=voteName, color=discord.Color.yellow()), view=view)
        view.set_self_message(message)

    @commands.command(name="vote3")
    async def sendVoteType3(self, ctx, voteName, voteTime, *labels): #채팅에 투표이름, 시간, 인자들 순서로 입력
        if self.set.command_allow_opt and (ctx.message.author.name not in self.set.command_allow):return #명령권한 설정이 되어 있는 경우 화이트리스트 확인
        view = VoteType3(self.bot, voteName, labels, int(voteTime)) #입력을 토대로 투표버튼 생성
        message = await ctx.send(embed = discord.Embed(title=voteName, color=discord.Color.yellow()), view=view)
        view.set_self_message(message)

    @commands.command(name="vote4")
    async def sendVoteType4(self, ctx, voteName, voteTime, *labels): #채팅에 투표이름, 시간, 인자들 순서로 입력
        if self.set.command_allow_opt and (ctx.message.author.name not in self.set.command_allow):return #명령권한 설정이 되어 있는 경우 화이트리스트 확인
        view = VoteType4(self.bot, voteName, labels, int(voteTime)) #입력을 토대로 투표버튼 생성
        message = await ctx.send(embed = discord.Embed(title=voteName, color=discord.Color.yellow()), view=view)
        view.set_self_message(message)

async def setup(bot):
    await bot.add_cog(Voter(bot))
